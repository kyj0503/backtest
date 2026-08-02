"""
Prometheus ticker_popularity_total 라벨 카디널리티 상한(P2-15) 회귀 테스트

**버그**:
app/services/portfolio_manager_service.py는
`TICKER_POPULARITY_TOTAL.labels(ticker=item.symbol).inc()`를 검증되지 않은
(또는 형식만 검증되고 존재 여부는 검증되지 않은) 사용자 입력으로 직접 호출했다.
Prometheus Counter는 한 번 생성된 라벨 조합을 프로세스 생명주기 동안 절대 GC하지
않으므로, 공격자가 매 요청마다 다른 문자열(형식은 유효하지만 실재하지 않는
티커, 혹은 asset_type='cash'의 임의 커스텀 이름)을 보내면 시계열이 무한정
늘어나 메모리를 고갈시킬 수 있다.

**수정**: app/monitoring/custom_metrics.py에 record_ticker_popularity() 헬퍼를
추가해 이 파일 밖에서 TICKER_POPULARITY_TOTAL에 라벨을 붙이는 유일한 진입점으로
삼았다. 내부적으로 최초 등장한 티커를 최대 _MAX_TRACKED_TICKERS개까지만 고유
라벨로 추적하고, 그 이후 처음 보는 티커는 전부 'other' 라벨로 합친다 -- 라벨
종류의 총 개수가 절대 _MAX_TRACKED_TICKERS + 1을 넘지 않는다. 이미 추적 중인
티커는 계속 자기 라벨로 집계되므로(인기 있는 실제 티커일수록 초반에 캡을 채울
가능성이 높다) "어떤 티커가 인기있는지" 라는 메트릭의 원래 목적은 유지된다.
현금 항목(asset_type='cash')은 애초에 "티커"가 아니므로
portfolio_manager_service.py에서 record_ticker_popularity() 호출 자체를
건너뛴다.
"""
import pytest

from app.monitoring import custom_metrics
from app.monitoring.custom_metrics import TICKER_POPULARITY_TOTAL, record_ticker_popularity

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def isolate_seen_tickers():
    """다른 테스트(또는 이전 실행)가 전역 _seen_tickers에 남긴 상태로부터
    격리한다. 모듈 레벨 카디널리티 상한은 프로세스 생명주기 동안 유지되는
    의도된 설계이므로, 테스트에서만 명시적으로 리셋한다."""
    custom_metrics._seen_tickers.clear()
    yield
    custom_metrics._seen_tickers.clear()


def _distinct_labels_with_prefix(prefix: str) -> set:
    return {
        labelvalues[0]
        for labelvalues in TICKER_POPULARITY_TOTAL._metrics.keys()
        if labelvalues[0].startswith(prefix)
    }


class TestTickerPopularityCardinalityBound:
    def test_many_distinct_junk_tickers_produce_bounded_label_count(self):
        """RED(수정 전): record_ticker_popularity 헬퍼가 없어 이 테스트 자체가
        ImportError로 실패한다. 수정 전 코드가 실제로 하던 일
        (TICKER_POPULARITY_TOTAL.labels(ticker=item.symbol).inc()를 직접 호출)로
        동일한 정크 티커들을 넣으면 cap보다 훨씬 많은(overflow개) 고유 라벨이
        생겨 이 assert가 실패했을 것이다."""
        cap = custom_metrics._MAX_TRACKED_TICKERS
        overflow = 300
        junk_tickers = [f"JUNKTICKER{i:06d}" for i in range(cap + overflow)]

        for ticker in junk_tickers:
            record_ticker_popularity(ticker)

        junk_labels = _distinct_labels_with_prefix("JUNKTICKER")
        assert len(junk_labels) <= cap, (
            f"정크 티커 라벨 수({len(junk_labels)})가 카디널리티 상한({cap})을 초과함"
        )

        other_value = TICKER_POPULARITY_TOTAL.labels(ticker=custom_metrics._OTHER_TICKER_LABEL)._value.get()
        assert other_value >= overflow, (
            f"상한을 넘긴 {overflow}개 이상이 'other' 버킷으로 집계되어야 하는데 "
            f"{other_value}만 집계됨"
        )

    def test_same_ticker_repeated_does_not_grow_cardinality(self):
        """같은 티커를 반복 호출해도 라벨은 하나만 생긴다 (정상적인 인기도 집계)."""
        for _ in range(50):
            record_ticker_popularity("AAPL")

        assert TICKER_POPULARITY_TOTAL.labels(ticker="AAPL")._value.get() >= 50

    def test_ticker_already_tracked_keeps_own_label_even_after_cap_reached(self):
        """캡이 다 찬 뒤에도, 이미 추적 중이던 티커는 계속 자기 라벨로 집계된다
        (인기 티커가 정크에 밀려 'other'로 뭉개지지 않는다)."""
        cap = custom_metrics._MAX_TRACKED_TICKERS
        record_ticker_popularity("MSFT")  # 캡을 채우기 전에 먼저 등록
        for i in range(cap + 50):
            record_ticker_popularity(f"FILLER{i:06d}")

        # MSFT는 캡이 다 찬 뒤에도 여전히 자기 라벨로 집계되어야 한다
        record_ticker_popularity("MSFT")
        assert TICKER_POPULARITY_TOTAL.labels(ticker="MSFT")._value.get() >= 2
