# 로컬 Python / Rust 비교 환경

최신 결과: [Yahoo 라이브러리 전환·회귀 검증·성능·메모리 재측정](../docs/reviews/rust-yahoo-client-2026-11-11.md). 현재 Rust는 Python의 잘못된 금융 출력을 보존하지 않는다. 아래 기존 비교 보고서는 이전 버전 기록이다.

동일 시세로 수행한 최신 API 계산 시간·메모리 벤치마크는 `./scripts/benchmark-frozen-memory.ps1`로 재실행한다. 보존된 `.comparison/reports/corrected-2026-11-11/benchmark-inputs`가 필요하다. 별도 컨테이너 2개를 사용하고 종료 시 정리하며, 네 사용자 서비스와 DB는 유지한다. 결과는 매번 새 디렉터리에 기록한다. 고정 시세 로딩·계산·JSON 응답 비용을 포함하며 Yahoo 네트워크·응답 해석과 DB 지연은 제외한다. Yahoo 수집 경로의 실조회 검증·시간·메모리는 별도의 `verify-yahoo-client.py`로 측정한다.

| 구현 | 프론트엔드 | 백엔드 |
| --- | --- | --- |
| 기존 Python | http://localhost:5173/backtest | http://localhost:8000 |
| Rust 이전본 | http://localhost:5174/backtest | http://localhost:8001 |

프론트엔드는 양쪽 모두 React다. Python 쪽은 이전 커밋의 소스를 `.comparison`에 내보내 빌드하고, Rust 쪽은 현재 작업 디렉터리를 빌드한다. 작업 브랜치를 변경하거나 미커밋 수정 사항을 이동하지 않는다.

- Python 백엔드 기준: `b7a284f81283db1a537d15a5b49cc892f7f039d7`
- 기존 프론트엔드 기준: `40931a59703b768c13c37071d3f7e41797a21ae9`
- 양쪽 프론트엔드에 동일한 로컬 프록시 설정을 추가하여 계산과 4개 참고 조회를 해당 백엔드로 전달한다. 이전 소스의 화면·계산 코드는 수정하지 않는다.
- 실제 Yahoo 시세를 조회한다. 합성 시세 파일을 사용하지 않는다.
- 앱 4개와 캐시용 MySQL 2개가 실행된다. 각 구현은 별도 DB 볼륨을 사용한다. 기존 개발·운영 DB에 연결하지 않는다.
- 두 API는 각각 CPU 2개, 메모리 2GB로 제한한다. 최초 조회와 캐시된 조회는 소요 시간이 다르므로 성능을 비교할 때 구분한다.
- 모든 공개 포트는 `127.0.0.1`에만 바인딩한다. 로컬 수동 비교를 위해 Turnstile은 끄고 프론트엔드는 Vite 개발 모드로 실행한다.
- 현재 로컬 네이버 인증값이 없어 뉴스는 빈 결과다. 주가·환율·벤치마크·백테스트 계산은 실제 데이터를 사용한다.

백엔드 저장소에서 PowerShell로 실행한다.

```powershell
# 최초 생성 또는 소스 변경 후 다시 빌드
./scripts/start-local-comparison.ps1

# 상태, 로그
docker compose -f compose.compare.yaml ps
docker compose -f compose.compare.yaml logs --tail 100 python-api rust-api

# 중지 / 다시 시작 (DB 캐시 유지)
docker compose -f compose.compare.yaml stop
docker compose -f compose.compare.yaml start

# 컨테이너와 네트워크 제거 (DB 볼륨 유지)
docker compose -f compose.compare.yaml down
```

브라우저 검증의 입력·응답·화면 캡처는 로컬 `.comparison/reports`에 저장한다. 이 디렉터리는 Git에서 제외한다.

최신 결과는 [수정 후 동작·성능 비교](results-fixed-2026-11-11.md)와 [수정 후 메모리 비교](memory-results-fixed-2026-11-11.md)를 참조한다. 환율 날짜·입력·응답 차이를 수정했고 동일 실데이터 32개 계산을 Python과 대조했다. 로컬 비교 DB의 시세를 한 번 맞춘 절차와 Yahoo 재조회에 따른 미세한 잔여 차이도 기록했다. [수정 전 비교](results-2026-11-11.md)는 이력으로 보존한다.

[추가 메모리 벤치마크](memory-results-2026-11-11.md)는 같은 이미지의 임시 API에서 요청 전·실행 중 관측 최대·완료 후 메모리와 커널의 전체 최대값을 측정한다. `./scripts/benchmark-local-memory.ps1`로 재실행하며, 기존 비교 스택과 저장된 정상 시나리오 입력이 필요하다.

수정 후 입력을 재사용하려면 `./scripts/benchmark-local-memory.ps1 -SamplesDirectory scenarios-final`을 실행한다. 보고서 디렉터리는 매번 새로 생성해 기존 결과를 보존한다.
