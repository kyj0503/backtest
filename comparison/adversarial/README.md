# 독립 계산 감사 재현

이 폴더는 Rust 서비스의 정확성을 현금 보존·시간 순서·독립 산술로 검사한다. 기존 Python 백테스트 서비스나 parity 기대값을 금융 정답으로 사용하지 않는다. `audit.py`의 Python은 합성 입력 생성과 단순 산술 판정만 수행한다.

[감사 보고서](C:/Users/serial/source/개인프로젝트/backtest/docs/reviews/rust-adversarial-audit-2026-11-11.md), [보존한 증거](C:/Users/serial/source/개인프로젝트/backtest/comparison/adversarial/evidence-2026-11-11.json).

현재 로컬 비교 환경에 준비된 `backtest-rust-toolchain:local`, `backtest-compare-rust-api:local`, `backtest-compare-rust-console:local`, `mysql:8.4` 이미지를 사용한다. 아래는 저장소 루트에서 실행하는 PowerShell 명령이다. 생성되는 크레이트와 대용량 원시 출력은 `.comparison` 아래에 둔다.

```powershell
$repo = 'C:\Users\serial\source\개인프로젝트\backtest'
$consoleRepo = 'C:\Users\serial\source\개인프로젝트\backtest-console'
$reportDir = "$repo\.comparison\reports\adversarial-2026-11-11"
$crateDir = "$repo\.comparison\adversarial-crate"
New-Item -ItemType Directory -Force -Path "$crateDir\examples" | Out-Null
Copy-Item -LiteralPath "$repo\backtest_be_rust\Cargo.toml","$repo\backtest_be_rust\Cargo.lock","$repo\backtest_be_rust\src","$repo\backtest_be_rust\openapi.json","$repo\backtest_be_rust\tests" -Destination $crateDir -Recurse -Force
Copy-Item -LiteralPath "$repo\comparison\adversarial\runner.rs" -Destination "$crateDir\examples\adversarial.rs"
Copy-Item -LiteralPath "$repo\comparison\adversarial\db_runner.rs" -Destination "$crateDir\examples\db_adversarial.rs"
python "$repo\comparison\adversarial\audit.py" prepare $reportDir

docker run --rm --mount "type=bind,source=$crateDir,target=/app" --mount type=volume,source=backtest-rust-cargo,target=/usr/local/cargo/registry --mount type=volume,source=backtest-rust-target,target=/app/target --mount "type=bind,source=$reportDir,target=/reports" --workdir /app backtest-rust-toolchain:local cargo run --offline --example adversarial -- /reports
python "$repo\comparison\adversarial\audit.py" evaluate $reportDir

docker run --rm --mount "type=bind,source=$consoleRepo,target=/src,readonly" --mount "type=bind,source=$repo\comparison\adversarial,target=/audit,readonly" --mount "type=bind,source=$reportDir,target=/reports" --workdir /app backtest-compare-rust-console:local node /audit/frontend.cjs
```

`evaluate`는 알려진 결함이 있어도 모든 검사를 완료하고 JSON에 `passed`를 기록한다. 프로세스 종료 코드 0은 금융 검사 전체 통과를 뜻하지 않는다. `checks.json`의 실패를 확인한다. 2026-11-11 실행은 133개 사례, 검사 201개 중 78개 불일치다.

실제 HTTP 경로는 기존 DB 없이 별도 컨테이너에서 검증한다. 이 단계는 포트 8002를 사용한다.

```powershell
python "$repo\comparison\adversarial\runtime_probe.py" prepare $reportDir
docker run -d --rm --name backtest-adversarial-http -p 127.0.0.1:8002:8000 -e DEBUG=true -e TURNSTILE_ENABLED=false -e BACKTEST_FIXTURE_FILE=/reports/http-fixtures.json --mount "type=bind,source=$reportDir,target=/reports,readonly" --cpus 2 --memory 512m backtest-compare-rust-api:local
python "$repo\comparison\adversarial\runtime_probe.py" run $reportDir
docker stop backtest-adversarial-http
```

DB 검사는 새 tmpfs 컨테이너만 사용한다. 이 블록의 schema/seed는 기존 DB에 실행하지 않는다. 아래 네트워크는 현재 로컬 비교 Compose가 만든 네트워크다. DB가 준비된 뒤 runner를 실행한다.

```powershell
docker run -d --rm --name backtest-adversarial-db --network backtest-compare_default --tmpfs /var/lib/mysql:rw,size=512m -e MYSQL_ROOT_PASSWORD=audit-only-root -e MYSQL_DATABASE=stock_data_cache -e MYSQL_USER=audit -e MYSQL_PASSWORD=audit-only --mount "type=bind,source=$repo\database\schema.sql,target=/docker-entrypoint-initdb.d/01-schema.sql,readonly" --mount "type=bind,source=$repo\comparison\adversarial\seed.sql,target=/docker-entrypoint-initdb.d/02-seed.sql,readonly" mysql:8.4
docker logs --tail 10 backtest-adversarial-db
docker run --rm --network backtest-compare_default -e AUDIT_DISPOSABLE_DATABASE=true -e DATABASE_URL=mysql://audit:audit-only@backtest-adversarial-db:3306/stock_data_cache --mount "type=bind,source=$crateDir,target=/app" --mount type=volume,source=backtest-rust-cargo,target=/usr/local/cargo/registry --mount type=volume,source=backtest-rust-target,target=/app/target --mount "type=bind,source=$reportDir,target=/reports" --workdir /app backtest-rust-toolchain:local cargo run --offline --example db_adversarial -- /reports/database-results.json
docker stop backtest-adversarial-db
```

`evidence-2026-11-11.json`은 최초 감사 기록으로 보존한다. `summarize`는 이 고정 파일을 생성한 최초 감사용 명령이므로 수정 후 재실행에는 사용하지 않는다. 수정 후 원시 출력은 다른 `reportDir`에 저장하고, 정확성 기준을 바꾼 부분과 새 결과를 별도로 기록한다.
