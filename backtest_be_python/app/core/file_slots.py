"""프로세스 간에 공유되는 동시 실행 슬롯 (A-04)

uvicorn `--workers N`은 서로 메모리를 공유하지 않는 프로세스 N개를 띄운다.
`asyncio.Semaphore`나 `threading.Semaphore`는 프로세스 로컬이라 상한이 워커 수만큼
곱해진다. 여기서는 슬롯 하나를 락 파일 하나로 표현하고 `fcntl.flock`의 배타
잠금으로 점유한다.

- **워커 수와 무관**: 같은 디렉터리의 같은 파일을 여는 모든 프로세스가 같은 락을
  다툰다. 컨테이너마다 /tmp가 따로이므로 기본 디렉터리는 곧 "컨테이너 전체" 상한이다.
- **크래시 안전**: flock은 파일 디스크립터에 묶여 있어 프로세스가 죽으면(SIGKILL
  포함) 커널이 자동으로 푼다. 워커가 재시작돼도 슬롯이 새지 않는다.
- **같은 프로세스 안에서도 배타적**: flock은 "열린 파일 설명(open file
  description)" 단위이므로 한 프로세스가 같은 파일을 두 번 열면 두 번째 잠금은
  실패한다. (fcntl/lockf의 POSIX 레코드 락은 같은 프로세스끼리는 충돌하지 않아
  이 용도에 쓸 수 없다.)
- **대기는 폴링**: 블로킹 flock은 스레드를 하나 붙잡으므로, 호출자는
  `try_acquire()`를 짧은 간격으로 재시도한다(app/services/backtest_runner.py).
  그래서 대기열 순서는 FIFO가 아니다.

MySQL `GET_LOCK` 슬롯도 검토했으나 채택하지 않았다: 작업 내내 DB 커넥션 하나를
붙잡아야 해서 워커당 6개(pool 4 + overflow 2)뿐인 풀을 잠식하고, 연결이 끊기면
락도 풀려 "실제 작업이 끝날 때까지 슬롯 유지"를 보장하지 못한다. 컨테이너를 여러
개로 늘려 전체 상한이 필요해지면 그때 다시 검토한다.

락 파일은 지우지 않는다. 잠금을 쥔 채 unlink하면 다른 프로세스가 같은 이름으로
새 파일(다른 inode)을 만들어 동시에 "같은 슬롯"을 쥐는 경쟁이 생긴다.
"""
from __future__ import annotations

import errno
import fcntl
import os
import random
import threading
from typing import List, Optional


class FileSlot:
    """점유 중인 슬롯. release()는 여러 번 호출해도 안전하다."""

    def __init__(self, fd: int, path: str) -> None:
        self._fd: Optional[int] = fd
        self.path = path
        self._lock = threading.Lock()

    @property
    def held(self) -> bool:
        return self._fd is not None

    def release(self) -> None:
        with self._lock:
            fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


class FileSlotPool:
    """`directory/<name>-<i>.lock` (i < size) 파일들로 만든 슬롯 풀."""

    def __init__(self, directory: str, name: str, size: int) -> None:
        if size < 1:
            raise ValueError(f"슬롯 수는 1 이상이어야 합니다: {size}")
        self.directory = directory
        self.name = name
        self.size = size
        os.makedirs(directory, mode=0o700, exist_ok=True)
        self._paths: List[str] = [
            os.path.join(directory, f"{name}-{i}.lock") for i in range(size)
        ]

    @property
    def paths(self) -> List[str]:
        return list(self._paths)

    def _try_lock(self, path: str) -> Optional[FileSlot]:
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            if exc.errno in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EACCES):
                return None
            raise
        return FileSlot(fd, path)

    def try_acquire(self) -> Optional[FileSlot]:
        """비어 있는 슬롯 하나를 즉시 점유한다. 모두 차 있으면 None."""
        # 시작 위치를 무작위로 해 모든 프로세스가 0번부터 부딪히지 않게 한다.
        start = random.randrange(self.size)
        for k in range(self.size):
            slot = self._try_lock(self._paths[(start + k) % self.size])
            if slot is not None:
                return slot
        return None

    def held_count(self) -> int:
        """지금 점유된 슬롯 수(진단·테스트용).

        비어 있는 슬롯을 잠깐 잠갔다 푸는 방식이라, 그 찰나에 다른 요청의
        try_acquire가 그 슬롯을 "사용 중"으로 보고 다음 슬롯/다음 폴링으로 넘어갈
        수 있다. 요청 경로에서 쓰지 말 것.
        """
        held = 0
        for path in self._paths:
            slot = self._try_lock(path)
            if slot is None:
                held += 1
            else:
                slot.release()
        return held
