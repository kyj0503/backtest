"""DatabaseConfig.log_info()의 print() 제거 회귀 테스트 (P3-22b)

버그: DatabaseConfig.log_info()는 logger.info()/logger.debug()로 연결 정보를
남긴 뒤, 동일한 정보를 print()로 다시 무조건 stdout에 출력했다. print()는
로깅 프레임워크의 레벨/핸들러 제어를 완전히 우회하므로 운영 환경에서 로그
레벨을 올려도 끌 수 없고, get_masked_url()로 마스킹되지 않는 값(예:
database_user)까지 컨테이너 표준출력에 항상 남는다.

결정: root/password 기본값 폴백(_load_from_components)은 로컬 개발 편의를
위해 유지한다 — DATABASE_URL이나 개별 환경 변수가 전혀 없을 때만 쓰이는
최후의 폴백이며, 이번 감사 대상은 "무조건 stdout에 출력되는 print()"이지
"기본값이 존재한다는 사실" 자체가 아니다. 대신 print() 호출만 제거한다:
비밀번호는 이미 get_masked_url()로 마스킹된 뒤에만 로거를 통해 노출되므로,
로거 호출만 남겨도 정보 손실이 없다.
"""
import logging
import pytest

from app.services.database.database_config import DatabaseConfig


pytestmark = pytest.mark.unit


@pytest.fixture
def config(monkeypatch):
    # 컨테이너 환경에는 실제 DATABASE_URL이 설정되어 있다. DatabaseConfig.__init__은
    # DATABASE_URL이 있으면 그것을 파싱해 개별 인자를 무시하므로, 이 테스트가
    # 명시적으로 넘기는 host/user 값이 실제로 쓰이도록 환경변수를 제거해야 한다.
    monkeypatch.delenv('DATABASE_URL', raising=False)
    return DatabaseConfig(
        database_host='testhost',
        database_port='3306',
        database_user='testuser',
        database_password='supersecret',
        database_name='testdb',
    )


class TestLogInfoDoesNotPrintToStdout:
    def test_log_info_writes_nothing_to_stdout(self, config, capsys):
        config.log_info()

        captured = capsys.readouterr()
        assert captured.out == '', f"print()가 여전히 stdout에 출력하고 있습니다: {captured.out!r}"

    def test_log_info_does_not_leak_raw_password_to_stdout(self, config, capsys):
        config.log_info()

        captured = capsys.readouterr()
        assert 'supersecret' not in captured.out


class TestLogInfoStillLogsViaLogger:
    def test_log_info_logs_connection_metadata_via_logger(self, config, caplog):
        with caplog.at_level(logging.INFO, logger='app.services.database.database_config'):
            config.log_info()

        messages = [record.getMessage() for record in caplog.records]
        assert any('testhost' in m for m in messages)
        assert any('testuser' in m for m in messages)

    def test_log_info_never_logs_raw_password(self, config, caplog):
        with caplog.at_level(logging.DEBUG, logger='app.services.database.database_config'):
            config.log_info()

        messages = [record.getMessage() for record in caplog.records]
        assert not any('supersecret' in m for m in messages), (
            "원본 비밀번호가 마스킹되지 않고 로그에 노출되었습니다."
        )
