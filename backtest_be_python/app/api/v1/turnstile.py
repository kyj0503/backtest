"""Validate human verification before accepting calculation work.

Only Cloudflare's Siteverify response is authoritative. No result/token cache:
Siteverify enforces expiry and single use, including across backend workers.
"""
import asyncio
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Annotated

from fastapi import Header, HTTPException, Request

from ...core.config import settings

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
DENIED = "사람 인증이 필요하거나 만료되었습니다. 다시 인증한 뒤 실행해 주세요."
UNAVAILABLE = "사람 인증을 확인할 수 없습니다. 잠시 후 다시 시도해 주세요."


def _siteverify(token: str, secret: str) -> dict:
    data = urllib.parse.urlencode({"secret": secret, "response": token}).encode("utf-8")
    request = urllib.request.Request(SITEVERIFY_URL, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=settings.turnstile_timeout_seconds) as response:
        # Never log responses or submitted credentials, even on failure.
        body = response.read(16_385)
    if len(body) > 16_384:
        raise ValueError("Oversized Siteverify response")
    result = json.loads(body)
    if not isinstance(result, dict):
        raise ValueError("Invalid Siteverify response")
    return result


async def require_turnstile(
    request: Request,
    token: Annotated[str | None, Header(alias="X-Turnstile-Token",
        description="Turnstile single-use token for the backtest action")] = None,
) -> None:
    if not settings.turnstile_enabled:
        return
    secret = settings.turnstile_secret_key.get_secret_value().strip()
    hosts = {host.strip() for host in settings.turnstile_allowed_hostnames.split(",") if host.strip()}
    if not secret or not hosts or not settings.turnstile_expected_action:
        raise HTTPException(503, UNAVAILABLE)
    if (not token or not token.strip() or len(token) > 2048
            or len(request.headers.getlist("X-Turnstile-Token")) != 1):
        raise HTTPException(403, DENIED)
    try:
        result = await asyncio.to_thread(_siteverify, token, secret)
    except (OSError, ValueError, urllib.error.URLError):
        # Fail closed; external errors must not reach the simulation/error decorator.
        raise HTTPException(503, UNAVAILABLE) from None
    if (result.get("success") is not True or not isinstance(result.get("hostname"), str)
            or result.get("hostname") not in hosts
            or result.get("action") != settings.turnstile_expected_action):
        raise HTTPException(403, DENIED)
