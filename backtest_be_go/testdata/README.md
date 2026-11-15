# testdata

Go 백엔드 테스트가 쓰는 고정 픽스처다. 모두 Python(develop) 구현이 만든 **회귀 기록**이며 합격 기준이 아니다.
합격 기준은 불변식(현금 보존, 체결 인과성, 수수료·PnL 항등식)이다. 기대값과 다른 결과는
`docs/go-migration-plan.md`의 F/R/S/T 수정 목록으로 설명되어야 하고, 설명되지 않는 차이는 버그로 본다.

**규칙: 어떤 파일도 Go 출력으로 재생성하지 않는다.**

## rust/

`rust-migration` 브랜치(`eef72a4`)의 `backtest_be_rust/tests/fixtures/`에서 그대로 복사했다
(`git show rust-migration:<path>`). 생성 기준은 develop `b7a284f`의 Python 구현 + backtesting.py 0.6.6이다
(`backtest_be_rust/tests/export_reference.py`, 네트워크 없는 Python 컨테이너).

| 파일 | 내용 |
|---|---|
| `histories.json` | 합성 일봉 6종(AAPL, MSFT, 005930.KS, KRW=X, ^GSPC, ^IXIC). 다른 픽스처의 입력 시세이자 E2E용 `BACKTEST_FIXTURE_FILE` |
| `parity.json` | 64개 요청과 Python 응답 `{name, request, expected}`. 현금, USD/KRW, 비중, 적립 6종, 리밸런싱, 휴장일, 전략 5종 포함 |
| `http-boundary.json` | 23개 HTTP 경계 요청과 Python 에러 응답 `{detail}` |
| `supplemental.json` | prices, exchange-rates, benchmarks 응답 |
| `real-market-python.json` | 실데이터 6개 사례 |
| `readversarial.json` | 재적대적 평가 사례 |
| `yahoo-chart-regression.json` | 실제 Yahoo chart 응답 7종, 일봉 90개. 파서 회귀용 |

## python/

develop의 `backtest_be_fast/tests/`에서 가져왔다. `scripts/export-python-reference.sh`가 Docker로 실행한다.

1. `--target test` 이미지 빌드. develop 테스트(579 unit, 1 e2e)가 통과해야 빌드된다.
2. `--network none`으로 `scripts/python-reference/export_inputs.py` 실행.
3. `verify_inputs.py` 실행. 내보낸 입력만으로 Python 응답이 스냅샷과 같게 재현되는지 확인한다.

| 파일 | 출처 |
|---|---|
| `golden/AAPL.csv`, `MSFT.csv`, `expected_dca_output.json` | `tests/e2e/data/` 원본 복사 |
| `golden/request.json` | `test_golden_master.py`의 payload와 mock 조건 (AAPL $1000 주간 DCA, 2023-01-01~02-28, USD) |
| `contract/api-contract.json` | `tests/unit/fixtures/` 원본. OpenAPI `paths` + `components` 스냅샷 |
| `snapshot/portfolio_manager_response_snapshot.json` | `tests/unit/data/` 원본. 시나리오 7개 |
| `snapshot/inputs.json` | buy&hold 시나리오 5개의 요청, 합성 종가, 통화, 환율, 로드 실패 종목 |

`snapshot`의 `strategy_*` 시나리오 2개는 backtesting.py 결과를 mock한 것이라 엔진 기준값으로 쓰지 않는다.
응답 키 순서 검증에만 쓸 수 있다.

`source_commit`은 `backtest_be_fast/`를 마지막으로 바꾼 커밋(`a00a858`)이다. develop HEAD `b7a284f`와 Python 코드가 같다.
