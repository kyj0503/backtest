"""
티커 인기 메트릭 라벨 정책 회귀 테스트 (A-18)

**문제**: P2-15는 ticker_popularity_total의 카디널리티를 "처음 본 티커 200개 +
other"로 묶었다. LRU도 재평가도 없는 first-N-seen이라, 프로세스 초반에 무작위
티커가 슬롯을 채우면 그 뒤에 들어온 실제 인기 티커는 전부 other로 합쳐진다.

**수정**:
1. 사전 허용 목록(TICKER_TO_COMPANY_NAME + 주요 ETF)은 항상 자기 라벨을 쓴다.
   모든 워커가 같은 목록을 쓰므로 멀티프로세스에서도 워커별 값이 한 라벨로 합쳐진다.
2. 목록 밖 티커는 한 번 봤다고 슬롯을 주지 않는다. Space-Saving 후보 표로 빈도를
   세고, "보장 횟수(count - error)"가 승격 기준 이상일 때만 동적 슬롯에 올린다.
   한 번씩만 나오는 무작위 티커는 후보 표가 가득 차 교체가 일어나도 보장 횟수가
   1을 넘지 못하므로 슬롯을 차지할 수 없다.
3. 동적 슬롯은 강등하지 않는다. prometheus_client는 멀티프로세스 모드에서 라벨
   삭제를 지원하지 않으므로(remove()가 경고만 내고 mmap 파일의 값은 남는다),
   강등해도 노출되는 시계열은 줄지 않고 상한만 깨진다. 재평가는 재배포(컨테이너
   재시작 시 entrypoint가 멀티프로세스 디렉터리를 비움) 때 자연히 일어난다.

운영 other 비율은 볼 수 없으므로 아래 시뮬레이션으로 개선 효과를 보인다.
"""
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry
from prometheus_client import multiprocess

from app.monitoring import custom_metrics
from app.monitoring.custom_metrics import TickerLabelPolicy

pytestmark = pytest.mark.unit

OTHER = custom_metrics._OTHER_TICKER_LABEL

# 허용 목록에 없는 "나중에 뜬" 인기 티커 (동적 슬롯으로 잡혀야 한다)
EMERGING_POPULAR = [f"HOT{i:02d}" for i in range(20)]
ALLOWLISTED_POPULAR = ["AAPL", "TSLA", "NVDA", "005930.KS", "SPY", "QQQ"]


class _FirstNSeenPolicy:
    """P2-15의 기존 정책 (비교 기준)."""

    def __init__(self, cap: int):
        self.cap = cap
        self.seen = set()

    def label_for(self, ticker: str) -> str:
        t = (ticker or "").strip().upper()
        if not t:
            return OTHER
        if t in self.seen:
            return t
        if len(self.seen) < self.cap:
            self.seen.add(t)
            return t
        return OTHER


def _traffic(seed: int = 7):
    """프로세스 초반에 무작위 티커 500개가 먼저 들어오고, 이후 인기 티커와
    잡음(한 번씩만 나오는 티커)이 섞여 들어오는 요청 흐름."""
    rng = random.Random(seed)
    stream = [f"RND{i:05d}" for i in range(500)]  # 초반 잡음
    popular = ALLOWLISTED_POPULAR + EMERGING_POPULAR
    weights = [1.0 / (rank + 1) for rank in range(len(popular))]  # Zipf
    noise_id = 10_000
    for _ in range(6000):
        if rng.random() < 0.2:
            stream.append(f"RND{noise_id:05d}")
            noise_id += 1
        else:
            stream.append(rng.choices(popular, weights=weights)[0])
    return stream


def _run(policy, stream):
    counts = {}
    for ticker in stream:
        label = policy.label_for(ticker)
        counts[label] = counts.get(label, 0) + 1
    return counts


class TestPopularTickersGetTheirOwnLabels:
    def test_popular_tickers_are_not_starved_by_early_random_tickers(self):
        """RED(수정 전): TickerLabelPolicy가 없다. 기존 first-N-seen 정책은
        초반 무작위 티커가 200 슬롯을 다 채워 인기 티커가 전부 other로 간다."""
        stream = _traffic()
        old = _run(_FirstNSeenPolicy(cap=200), stream)
        new = _run(TickerLabelPolicy(), stream)
        total = len(stream)

        old_other_ratio = old.get(OTHER, 0) / total
        new_other_ratio = new.get(OTHER, 0) / total
        popular = ALLOWLISTED_POPULAR + EMERGING_POPULAR

        # 기존 정책: 인기 티커 중 자기 라벨을 가진 것이 하나도 없다
        assert not any(t in old for t in popular)
        # 새 정책: 인기 티커가 전부 자기 라벨을 갖는다
        missing = [t for t in popular if t not in new]
        assert not missing, f"인기 티커가 other로 묶였다: {missing}"
        # other에는 잡음(약 20% + 초반 500개)과 승격 전 몇 번만 남는다
        assert new_other_ratio < 0.30, new_other_ratio
        assert old_other_ratio > 0.85, old_other_ratio

    def test_allowlisted_ticker_is_labelled_from_the_first_request(self):
        policy = TickerLabelPolicy()
        assert policy.label_for("aapl") == "AAPL"
        assert policy.label_for(" 005930.ks ") == "005930.KS"
        assert policy.label_for("SPY") == "SPY"

    def test_unlisted_ticker_is_promoted_after_min_count_requests(self):
        policy = TickerLabelPolicy(min_count=3)
        assert policy.label_for("ZZZZ") == OTHER
        assert policy.label_for("ZZZZ") == OTHER
        assert policy.label_for("ZZZZ") == "ZZZZ"
        assert policy.label_for("ZZZZ") == "ZZZZ"

    def test_blank_ticker_goes_to_other(self):
        policy = TickerLabelPolicy()
        assert policy.label_for("") == OTHER
        assert policy.label_for("   ") == OTHER
        assert policy.label_for(None) == OTHER


class TestCardinalityStaysBounded:
    def test_one_off_tickers_are_never_promoted_even_when_candidate_table_overflows(self):
        """Space-Saving 교체 시 새 항목은 이전 최소값을 '오차'로 물려받는다.
        보장 횟수(count - error)로 판단하지 않으면 한 번만 나온 티커도 부풀려진
        count로 승격될 수 있다."""
        policy = TickerLabelPolicy(candidate_capacity=50, min_count=3)
        labels = {policy.label_for(f"ONEOFF{i:06d}") for i in range(20_000)}
        assert labels == {OTHER}

    def test_squatting_attack_cannot_exceed_the_bound(self):
        """공격자가 매 티커를 승격 기준만큼 반복해 보내도 라벨 수는 상한 안이다."""
        policy = TickerLabelPolicy(max_dynamic=30, min_count=3)
        labels = set()
        for i in range(2_000):
            for _ in range(3):
                labels.add(policy.label_for(f"SQUAT{i:05d}"))
        for ticker in ALLOWLISTED_POPULAR:
            labels.add(policy.label_for(ticker))

        dynamic = {label for label in labels if label.startswith("SQUAT")}
        assert len(dynamic) <= 30
        # 허용 목록은 동적 슬롯이 다 차도 영향받지 않는다
        assert set(ALLOWLISTED_POPULAR) <= labels

    def test_global_label_bound_formula(self):
        policy = TickerLabelPolicy(max_dynamic=30)
        assert policy.max_labels == len(policy.allowlist) + 30 + 1


class TestRecordTickerPopularityUsesThePolicy:
    def test_record_uses_module_policy(self, monkeypatch):
        policy = TickerLabelPolicy(min_count=2)
        monkeypatch.setattr(custom_metrics, "_ticker_label_policy", policy)
        counter = custom_metrics.TICKER_POPULARITY_TOTAL
        before = counter.labels(ticker="NEWCO")._value.get()
        custom_metrics.record_ticker_popularity("NEWCO")  # 1회: other
        custom_metrics.record_ticker_popularity("NEWCO")  # 2회: 승격
        assert counter.labels(ticker="NEWCO")._value.get() == before + 1


_WORKER_SCRIPT = r"""
import json, sys
from app.monitoring.custom_metrics import record_ticker_popularity, _ticker_label_policy
stream = json.loads(sys.argv[1])
for t in stream:
    record_ticker_popularity(t)
print(json.dumps({"allowlist": len(_ticker_label_policy.allowlist),
                  "max_dynamic": _ticker_label_policy.max_dynamic}))
"""


class TestMultiprocessMode:
    def test_worker_values_are_summed_and_labels_stay_bounded(self, tmp_path):
        """uvicorn --workers N + PROMETHEUS_MULTIPROC_DIR 조합을 흉내 낸다.
        워커마다 정책 상태가 따로라 동적 승격은 워커별로 일어나지만, 허용 목록
        라벨은 모든 워커가 같아서 /metrics에서 한 시계열로 합쳐진다."""
        mp_dir = tmp_path / "prom"
        mp_dir.mkdir()
        env = dict(os.environ, PROMETHEUS_MULTIPROC_DIR=str(mp_dir))
        be_root = Path(__file__).resolve().parents[2]

        workers = 2
        streams = []
        for w in range(workers):
            stream = ["AAPL"] * 5 + [f"W{w}ONEOFF{i}" for i in range(300)]
            stream += [f"W{w}SQUAT{i:04d}" for i in range(200) for _ in range(3)]
            streams.append(stream)

        meta = None
        for stream in streams:
            out = subprocess.run(
                [sys.executable, "-c", _WORKER_SCRIPT, json.dumps(stream)],
                cwd=be_root, env=env, capture_output=True, text=True, timeout=120,
            )
            assert out.returncode == 0, out.stderr[-2000:]
            meta = json.loads(out.stdout.strip().splitlines()[-1])

        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry, path=str(mp_dir))
        samples = {
            s.labels["ticker"]: s.value
            for metric in registry.collect()
            if metric.name == "ticker_popularity"
            for s in metric.samples
            if s.name == "ticker_popularity_total"
        }

        total_recorded = sum(len(s) for s in streams)
        assert sum(samples.values()) == total_recorded
        assert samples["AAPL"] == 5 * workers, "허용 목록 라벨이 워커 간에 합쳐지지 않음"
        bound = meta["allowlist"] + workers * meta["max_dynamic"] + 1
        assert len(samples) <= bound, (len(samples), bound)
        assert not any("ONEOFF" in label for label in samples), "한 번만 나온 티커가 라벨이 됨"
