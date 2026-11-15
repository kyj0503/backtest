"""신뢰할 수 있는 클라이언트 IP 식별 (A-06)

**운영 경로** (저장소 기준으로 확인한 것):

    브라우저 → home-server nginx → FE 컨테이너 nginx(nginx.prod.conf) → BE(uvicorn)

`backtest_fe/nginx.prod.conf`의 `/api/v1/backtest` location은
`X-Forwarded-For $proxy_add_x_forwarded_for`(받은 XFF 뒤에 자신이 본 원격 주소를
덧붙임)와 `X-Real-IP $remote_addr`를 보낸다. FE nginx가 보는 `$remote_addr`는
home-server nginx(사설 도커망 주소)이므로 **X-Real-IP는 클라이언트가 아니다.**
home-server nginx 설정은 이 저장소 밖이라 확인할 수 없다 — 표준 설정
(`$proxy_add_x_forwarded_for`)이면 XFF는 `<클라이언트가 보낸 값...>, <실제 클라이언트>,
<home-server nginx>` 모양이 된다.

**판정 규칙 — "오른쪽부터 첫 번째 비신뢰 주소"**:
1. TCP 피어(request.client.host)가 신뢰 프록시 대역이 아니면 그것이 곧 클라이언트다.
   이때 XFF는 **보지 않는다**(프록시 없이 직접 붙은 클라이언트가 헤더를 위조할 수 있음).
2. 피어가 신뢰 프록시면 XFF를 오른쪽부터 읽으며 신뢰 대역을 건너뛰고, 처음 만나는
   비신뢰 주소를 클라이언트로 본다. 그보다 왼쪽은 클라이언트가 임의로 채울 수 있는
   값이라 절대 쓰지 않는다. 가장 왼쪽 값을 쓰는 흔한 구현은 `X-Forwarded-For: 1.2.3.4`
   한 줄로 요청마다 다른 IP를 사칭할 수 있어 IP별 제한이 무력화된다.
3. 끝까지 신뢰 대역뿐이거나(사설망 클라이언트, 또는 앞단 프록시가 XFF를 넘기지
   않는 경우) 형식이 깨진 항목을 만나면 **식별 불가(None)** 로 본다. 호출자는 이때
   IP별 제한을 적용하지 않는다(fail-open). 모든 요청이 프록시 주소 하나로 묶여
   서비스 전체가 "IP당 2건"으로 막히는 사고를 피하기 위함이며, 컨테이너 전체 상한은
   그대로 적용된다.

신뢰 대역 기본값은 루프백 + 사설망이다(config.trusted_proxy_cidrs). 사설망 클라이언트
(같은 LAN)는 3번 규칙에 따라 IP별 제한을 받지 않는다 — 운영자 본인 LAN이라 허용한다.

IPv6 주소는 /64 단위로 묶는다. 가정용 회선도 보통 /64 이상을 받으므로 주소 하나
단위로 세면 한 사용자가 주소를 바꿔 가며 제한을 우회할 수 있다.
"""
from __future__ import annotations

import ipaddress
import logging
from typing import Iterable, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

IPNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


def parse_trusted_networks(spec: str) -> List[IPNetwork]:
    """쉼표로 구분된 CIDR 목록을 파싱한다. 잘못된 항목은 경고 후 무시."""
    networks: List[IPNetwork] = []
    for raw in (spec or "").split(","):
        item = raw.strip()
        if not item:
            continue
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            logger.warning("trusted_proxy_cidrs의 잘못된 항목 무시: %r", item)
    return networks


def _parse_ip(value: Optional[str]) -> Optional[IPAddress]:
    if not value:
        return None
    text = value.strip()
    # "[2001:db8::1]:443" / "1.2.3.4:5678" 같은 포트 포함 표기도 받아 준다.
    if text.startswith("[") and "]" in text:
        text = text[1:text.index("]")]
    elif text.count(":") == 1 and "." in text:
        text = text.split(":", 1)[0]
    try:
        ip = ipaddress.ip_address(text)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


def _is_trusted(ip: IPAddress, trusted: Sequence[IPNetwork]) -> bool:
    return any(ip.version == net.version and ip in net for net in trusted)


def resolve_client_ip(
    peer: Optional[str],
    forwarded_for: Optional[Iterable[str]],
    trusted: Sequence[IPNetwork],
) -> Optional[str]:
    """클라이언트 IP 문자열을 반환한다. 식별할 수 없으면 None.

    forwarded_for: X-Forwarded-For 헤더 값들(여러 줄이면 순서대로 이어 붙인다).
    """
    peer_ip = _parse_ip(peer)
    if peer_ip is None:
        # 유닉스 소켓이나 테스트 클라이언트("testclient")처럼 IP가 아닌 피어.
        # 프록시를 거쳤는지 알 수 없으므로 헤더는 믿지 않고 피어 문자열 자체를 쓴다.
        return peer.strip() if peer and peer.strip() else None
    if not _is_trusted(peer_ip, trusted):
        return str(peer_ip)

    chain: List[str] = []
    for header in forwarded_for or ():
        chain.extend(part.strip() for part in header.split(","))
    for entry in reversed(chain):
        if not entry:
            continue
        ip = _parse_ip(entry)
        if ip is None:
            return None  # 신뢰 프록시가 넣었을 리 없는 값 — 위조로 간주
        if not _is_trusted(ip, trusted):
            return str(ip)
    return None


def client_limit_key(client_ip: Optional[str]) -> Optional[str]:
    """IP별 제한에 쓸 키. IPv6는 /64로 묶는다."""
    if not client_ip:
        return None
    ip = _parse_ip(client_ip)
    if ip is None:
        return client_ip
    if isinstance(ip, ipaddress.IPv6Address):
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)
