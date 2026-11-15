"""compute_stats 몽키패치 제거 회귀 테스트 (P3-21a)

버그: backtest_service.py는 모듈 임포트 시점(top-level 코드)에
backtesting._stats.compute_stats를 감싸서, 특정 pandas Timedelta 비교 오류
("'>=' not supported between instances of 'float' and 'Timedelta'")가 발생하면
원본 예외를 삼키고 하드코딩된 조작 통계(Win Rate 50%, Profit Factor 1.0,
Sharpe/Sortino/Calmar 0.0 등)를 담은 pd.Series를 반환했다. 이 값은 그대로
HTTP 200 성공 응답으로 서빙된다.

도달 가능성: backtesting._stats.compute_stats는 backtesting 패키지 전역에
공유되는 함수 객체이므로, backtest_service 모듈이 어디서든 한 번 임포트되면
패치가 전역적으로 적용되어 이후 모든 백테스트 실행(단일/포트폴리오 무관, 실제
실행은 backtest_engine.py의 bt.run()이 담당하더라도)에 영향을 준다.
app/services/portfolio_manager_service.py:21이 모듈 최상단에서
`from app.services.backtest_service import backtest_service`를 수행하고,
portfolio_manager_service는 POST /api/v1/backtest의 실제 처리 체인
(app/api/v1/endpoints/backtest.py -> portfolio_manager_service)에 있으므로
이 몽키패치는 실제 운영 경로에서 도달 가능하다 (죽은 코드 아님).

수정: 몽키패치를 제거한다. compute_stats 오류는 이제 원본 그대로 전파되어
BacktestEngine.run_backtest()의 예외 처리기가 500으로 매핑한다 (가짜 200 성공
대신 실제 실패로 표면화).
"""
import pytest


pytestmark = pytest.mark.unit


class TestComputeStatsIsNotMonkeypatched:
    def test_compute_stats_is_not_wrapped_by_backtest_service(self):
        """backtest_service를 임포트해도 backtesting._stats.compute_stats가
        patched_compute_stats로 교체되어 있으면 안 된다."""
        import app.services.backtest_service  # noqa: F401  (임포트 부작용 확인용)
        import backtesting._stats as stats_module

        assert stats_module.compute_stats.__name__ != 'patched_compute_stats', (
            "backtest_service가 여전히 backtesting._stats.compute_stats를 감싸고 "
            "있습니다 — Timedelta 오류가 조작된 통계로 삼켜집니다."
        )

    def test_backtest_service_module_no_longer_defines_patch_function(self):
        """재도입 방지 가드: 몽키패치 함수 자체가 모듈에서 사라졌는지 확인한다."""
        import app.services.backtest_service as svc_module

        assert not hasattr(svc_module, '_patch_backtesting_stats'), (
            "_patch_backtesting_stats가 여전히 정의되어 있습니다."
        )
