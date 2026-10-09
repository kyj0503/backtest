#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
app=${1:?}
environment=${2:?}
image=${3:?}
revision=${4:?}
registry_user=${5:?}
case "$app" in backtest) container=backtest-be ;; backtest-console) container=backtest-fe ;; *) exit 2 ;; esac
case "$environment" in production|development) ;; *) exit 2 ;; esac
[[ "$image" =~ ^ghcr\.io/kyj0503/$app@sha256:[a-f0-9]{64}$ ]] || exit 2
[[ "$revision" =~ ^[a-f0-9]{40}$ ]] || exit 2
root="/opt/$app/$environment"
release=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
[[ "$release" == "$root"/releases/release.* ]] || exit 2
backend=backtest-be
if [[ "$environment" == development ]]; then container+="-dev"; backend+="-dev"; fi
project="$app-$environment"
exec 9>"$root/deploy.lock"
flock -w 300 9
previous=$(readlink -f "$root/current" || true)
legacy=""
changed=false
compose() { local directory=$1; shift; docker compose --env-file "$directory/deployment.env" -f "$directory/compose.yaml" "$@"; }
reload_gateway() { docker exec nginx-gateway nginx -t; docker exec nginx-gateway nginx -s reload; }
cleanup() { rm -f "$release/.registry-token"; rm -rf "$release/.docker"; }
failed() {
    local code=$?
    trap - ERR
    echo "Deployment failed (exit $code); restoring the previous deployment." >&2
    if [[ "$changed" == true ]]; then
        if [[ -n "$legacy" ]] && docker container inspect "$legacy" >/dev/null 2>&1; then
            compose "$release" rm -s -f app
            docker rename "$legacy" "$container"
            docker update --restart unless-stopped "$container" >/dev/null
            docker start "$container" >/dev/null
        elif [[ -n "$legacy" ]]; then
            docker start "$container" >/dev/null
        elif [[ -n "$previous" && -f "$previous/compose.yaml" ]]; then
            compose "$previous" up -d --no-deps --pull never --wait --wait-timeout 180 app
        else
            compose "$release" rm -s -f app
        fi
        reload_gateway
    fi
    exit "$code"
}
trap cleanup EXIT
trap failed ERR
if [[ "$app" == backtest ]]; then test -s "$root/.env"; fi
docker network inspect backend-net >/dev/null
mkdir -m 700 "$release/.docker"
export DOCKER_CONFIG="$release/.docker"
docker login ghcr.io -u "$registry_user" --password-stdin < "$release/.registry-token"
rm -f "$release/.registry-token"
docker pull "$image"
test "$(docker image inspect "$image" --format '{{.Architecture}}')" = arm64
test "$(docker image inspect "$image" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "$revision"
printf 'APP_ENV=%s\nAPP_CONTAINER=%s\nAPP_IMAGE=%s\nAPP_ENV_FILE=%s/.env\nAPP_BACKEND=%s:8000\n' \
    "$environment" "$container" "$image" "$root" "$backend" > "$release/deployment.env"
compose "$release" config --quiet
if docker container inspect "$container" >/dev/null 2>&1; then
    owner=$(docker inspect "$container" --format '{{index .Config.Labels "com.docker.compose.project"}}')
    if [[ "$owner" != "$project" ]]; then
        legacy="$container-pre-actions-$(date +%s)"
        changed=true
        docker stop "$container" >/dev/null
        docker rename "$container" "$legacy"
        docker update --restart no "$legacy" >/dev/null
    elif [[ ! -f "$previous/compose.yaml" ]]; then
        echo 'Current release metadata missing; refusing an untracked replacement.' >&2
        exit 1
    fi
fi
changed=true
compose "$release" up -d --no-deps --pull never --wait --wait-timeout 180 app
test "$(docker inspect "$container" --format '{{.Config.Image}}')" = "$image"
if [[ "$app" == backtest ]]; then
    # A running process alone is insufficient: DB connectivity must pass too.
    docker exec "$container" curl -fsS --max-time 10 http://localhost:8000/health/ready >/dev/null
else
    docker exec "$container" curl -fsS --max-time 10 http://localhost/ >/dev/null
fi
reload_gateway
ln -sfn "$release" "$root/current"
if [[ -n "$legacy" ]]; then printf '%s\n' "$legacy" > "$release/previous-container"; fi
echo "Deployed $container at $image (revision $revision)."
