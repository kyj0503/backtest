"""클라이언트 IP 식별(A-06)과 프로세스 공유 파일 락 슬롯(A-04) 단위 테스트"""
import multiprocessing
import os
import signal
import time

import pytest

from app.core.client_ip import client_limit_key, parse_trusted_networks, resolve_client_ip
from app.core.file_slots import FileSlotPool

pytestmark = pytest.mark.unit

TRUSTED = parse_trusted_networks(
    "127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fc00::/7"
)


class TestResolveClientIp:
    def test_untrusted_peer_is_the_client_and_headers_are_ignored(self):
        assert resolve_client_ip("203.0.113.9", ["1.1.1.1"], TRUSTED) == "203.0.113.9"

    def test_rightmost_untrusted_hop_behind_proxies(self):
        # 브라우저 → home-server nginx → FE nginx → BE (피어 = FE nginx)
        xff = ["6.6.6.6, 198.51.100.7, 172.18.0.2"]
        assert resolve_client_ip("172.18.0.5", xff, TRUSTED) == "198.51.100.7"

    def test_multiple_header_lines_are_concatenated_in_order(self):
        assert resolve_client_ip("10.0.0.2", ["6.6.6.6", "198.51.100.7, 10.0.0.9"], TRUSTED) == "198.51.100.7"

    def test_all_trusted_or_missing_means_unidentifiable(self):
        assert resolve_client_ip("172.18.0.5", None, TRUSTED) is None
        assert resolve_client_ip("172.18.0.5", ["192.168.0.10, 172.18.0.2"], TRUSTED) is None

    def test_garbage_left_of_trusted_hops_is_not_used(self):
        assert resolve_client_ip("172.18.0.5", ["not-an-ip, 172.18.0.2"], TRUSTED) is None

    def test_non_ip_peer_is_used_verbatim(self):
        assert resolve_client_ip("testclient", ["1.1.1.1"], TRUSTED) == "testclient"

    def test_ports_and_ipv4_mapped_addresses_are_normalised(self):
        assert resolve_client_ip("::ffff:203.0.113.9", None, TRUSTED) == "203.0.113.9"
        assert resolve_client_ip("10.0.0.2", ["203.0.113.9:5555"], TRUSTED) == "203.0.113.9"
        assert resolve_client_ip("10.0.0.2", ["[2001:db8::1]:443"], TRUSTED) == "2001:db8::1"

    def test_bad_cidr_entries_are_ignored(self):
        nets = parse_trusted_networks("10.0.0.0/8, nonsense ,")
        assert len(nets) == 1


class TestClientLimitKey:
    def test_ipv6_is_grouped_by_64(self):
        assert client_limit_key("2001:db8:1:2:aaaa::1") == client_limit_key("2001:db8:1:2:bbbb::2")
        assert client_limit_key("2001:db8:1:2::1") != client_limit_key("2001:db8:1:3::1")

    def test_ipv4_and_none(self):
        assert client_limit_key("203.0.113.9") == "203.0.113.9"
        assert client_limit_key(None) is None


class TestFileSlotPool:
    def test_size_limits_holders_even_inside_one_process(self, tmp_path):
        pool = FileSlotPool(str(tmp_path), "slot", 2)
        a, b = pool.try_acquire(), pool.try_acquire()
        assert a is not None and b is not None
        assert pool.try_acquire() is None
        assert pool.held_count() == 2
        a.release()
        a.release()  # 두 번 불러도 안전
        c = pool.try_acquire()
        assert c is not None
        b.release()
        c.release()
        assert pool.held_count() == 0

    def test_two_pool_objects_on_the_same_directory_share_capacity(self, tmp_path):
        """워커 프로세스마다 풀 객체가 따로 생겨도 같은 디렉터리면 같은 상한."""
        p1 = FileSlotPool(str(tmp_path), "slot", 1)
        p2 = FileSlotPool(str(tmp_path), "slot", 1)
        held = p1.try_acquire()
        assert held is not None
        assert p2.try_acquire() is None
        held.release()
        assert p2.try_acquire() is not None

    def test_slot_held_by_killed_process_is_released_by_the_os(self, tmp_path):
        from tests.unit.backtest_runner_mp_helper import hold_slot_until_killed

        ready = tmp_path / "ready"
        ctx = multiprocessing.get_context("spawn")
        proc = ctx.Process(
            target=hold_slot_until_killed, args=(str(tmp_path), "slot", 1, str(ready))
        )
        proc.start()
        try:
            deadline = time.monotonic() + 30
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            assert ready.exists(), "자식 프로세스가 슬롯을 잡지 못함"

            pool = FileSlotPool(str(tmp_path), "slot", 1)
            assert pool.try_acquire() is None, "다른 프로세스가 쥔 슬롯이 보이지 않는다"

            os.kill(proc.pid, signal.SIGKILL)  # 워커 크래시
            proc.join(timeout=10)
            slot = pool.try_acquire()
            assert slot is not None, "죽은 프로세스의 슬롯이 반환되지 않았다"
            slot.release()
        finally:
            if proc.is_alive():
                proc.kill()
                proc.join()
