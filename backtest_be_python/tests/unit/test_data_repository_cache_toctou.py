"""메모리 캐시(TTLCache) TOCTOU 회귀 테스트 (P3-20c)

버그: YfinanceDataRepository.get_stock_data()는
`if cache_key in self._memory_cache: return self._memory_cache[cache_key]`
패턴을 사용했다. TTLCache는 항목의 TTL이 지나면 스스로 만료시키는데, `in` 검사와
`[]` 조회는 별개의 두 호출이라 그 사이에 흐른 실제 시간(사이에 낀
self.logger.debug() 호출 등)만큼 TTL이 지나버리면 `in`은 True를 반환했지만
`[]`는 KeyError를 던질 수 있다. 이는 스레드 경합이 아니라 "두 호출 사이의 시간
경과"로 발생하는 TOCTOU라서, 이벤트 루프가 단일 스레드라는 사실과 무관하게
발생할 수 있다.

이 KeyError는 get_stock_data() 자신의 `except Exception as e: ... raise`에
그대로 재발생되어, 정상적으로 캐시 히트(또는 DB/yfinance로의 자연스러운 폴백)로
처리되어야 할 요청이 500 에러로 끝나 버린다.

수정: `.get(key, sentinel)`으로 존재확인과 조회를 하나의 원자적 호출로 묶는다.

테스트 방법: __contains__는 True를 반환하지만 __getitem__은 KeyError를 던지는
가짜 캐시 객체로 실제 TTLCache의 TOCTOU 상황을 재현한다. get()은 표준
Mapping.get() 시맨틱(내부에서 __getitem__을 감싸 KeyError를 처리)을 그대로
따르므로, 구현이 .get()을 사용하기만 하면 이 레이스가 사라진다.
"""
import pytest
import pandas as pd
from unittest.mock import Mock

from app.repositories.data_repository import YfinanceDataRepository


pytestmark = pytest.mark.unit


class ExpiresBetweenContainsAndGetitem:
    """멤버십 검사 시점엔 존재하지만, 그 직후 접근 시점엔 만료된 것처럼 동작하는
    테스트 더블. 실제 TTLCache가 두 호출 사이의 시간 경과로 겪을 수 있는
    TOCTOU 상황을 결정론적으로 재현한다."""

    def __init__(self):
        self._store = {}

    def __contains__(self, key):
        return True  # 존재확인 시점: 아직 만료되지 않았다고 응답

    def __getitem__(self, key):
        raise KeyError(key)  # 조회 시점: 그 사이 만료되어 사라졌다

    def get(self, key, default=None):
        # 표준 Mapping.get() 시맨틱: __getitem__을 단일 호출로 감싸 KeyError를
        # default로 변환한다. in-then-[] 패턴과 달리 호출이 하나뿐이라 TOCTOU가
        # 없다.
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        self._store[key] = value


@pytest.fixture
def repository():
    repo = YfinanceDataRepository()
    repo.data_fetcher = Mock()
    repo.stock_repository = Mock()
    return repo


@pytest.fixture
def sample_data():
    return pd.DataFrame({'Close': [100.0, 101.0, 102.0]})


class TestMemoryCacheTOCTOU:
    @pytest.mark.asyncio
    async def test_expiry_between_membership_check_and_read_does_not_raise(
        self, repository, sample_data
    ):
        """캐시 항목이 존재확인 직후 만료되어도 KeyError가 새어나가면 안 되고,
        DB 캐시로 안전하게 폴백해야 한다."""
        repository._memory_cache = ExpiresBetweenContainsAndGetitem()
        repository.stock_repository.load_stock_data = Mock(return_value=sample_data)

        result = await repository.get_stock_data('AAPL', '2023-01-01', '2023-01-31')

        pd.testing.assert_frame_equal(result, sample_data)

    @pytest.mark.asyncio
    async def test_expiry_race_falls_through_to_yfinance_when_db_also_misses(
        self, repository, sample_data
    ):
        """DB 캐시도 비어 있으면 (TOCTOU로 새어나간 예외 없이) yfinance까지
        정상적으로 폴백해야 한다."""
        repository._memory_cache = ExpiresBetweenContainsAndGetitem()
        repository.stock_repository.load_stock_data = Mock(return_value=None)
        repository.stock_repository.save_stock_data = Mock(return_value=3)
        repository.data_fetcher.fetch_stock_data = Mock(return_value=sample_data)

        result = await repository.get_stock_data('MSFT', '2023-02-01', '2023-02-28')

        pd.testing.assert_frame_equal(result, sample_data)
        repository.data_fetcher.fetch_stock_data.assert_called_once()
