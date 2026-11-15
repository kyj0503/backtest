# syntax=docker/dockerfile:1
#
# 스테이지:
#   toolchain   - Go 툴체인 + 모듈 다운로드 + 소스 (다른 스테이지의 공통 기반)
#   test        - gofmt / go vet / staticcheck / go test -race. CI가 --target test로 실행한다.
#   audit       - govulncheck. CI가 --target audit로 실행한다.
#   development - compose.dev.yaml이 쓰는 개발 이미지 (소스는 바인드 마운트, go run)
#   builder     - 정적 바이너리 빌드 (CGO 없음)
#   runtime     - distroless/static nonroot + 바이너리만. 기본 빌드 타깃(마지막 스테이지).
#
# 모든 빌드·테스트는 이 Dockerfile로 한다. 호스트에서 go 명령을 직접 실행하지 않는다.
ARG GO_IMAGE=golang:1.27.4-trixie
ARG RUNTIME_IMAGE=gcr.io/distroless/static-debian13:nonroot

FROM ${GO_IMAGE} AS toolchain
WORKDIR /src
ENV GOTOOLCHAIN=local GOFLAGS=-mod=readonly
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download && go mod verify
COPY . .

FROM toolchain AS test
ARG STATICCHECK_VERSION=v0.8.2
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    GOFLAGS= go install honnef.co/go/tools/cmd/staticcheck@${STATICCHECK_VERSION}
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build <<'EOF'
set -eu
unformatted="$(gofmt -l .)"
if [ -n "$unformatted" ]; then echo "gofmt needed:"; echo "$unformatted"; exit 1; fi
go vet ./...
staticcheck ./...
CGO_ENABLED=1 go test -race -count=1 ./...
EOF

FROM toolchain AS audit
ARG GOVULNCHECK_VERSION=v1.9.0
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    GOFLAGS= go install golang.org/x/vuln/cmd/govulncheck@${GOVULNCHECK_VERSION} && govulncheck ./...

FROM toolchain AS development
ENV CGO_ENABLED=0
EXPOSE 8000
CMD ["go", "run", "./cmd/server"]

FROM toolchain AS builder
ARG IMAGE_TAG=dev
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/ ./cmd/server ./cmd/backtestctl

FROM ${RUNTIME_IMAGE} AS runtime
ARG IMAGE_TAG=latest
ENV IMAGE_TAG=${IMAGE_TAG} IMAGE_NAME=backtest-backend PORT=8000
COPY --from=builder /out/server /out/backtestctl /app/
WORKDIR /app
EXPOSE 8000
# liveness(/health)에 건다. readiness(/health/ready)는 배포 후 확인 단계가 직접 본다.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD ["/app/server", "-healthcheck", "/health"]
USER nonroot:nonroot
ENTRYPOINT ["/app/server"]
