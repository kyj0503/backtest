#!/usr/bin/env python3
"""파일의 특정 라인을 수정하는 스크립트"""
import sys

# 파일 읽기
with open('/home/kyj/source/backtest/backtest_be_fast/app/utils/data_fetcher.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 197-202번 라인 수정 (0-indexed이므로 196-201)
new_lines = [
    "        # 숫자로만 구성되거나 무효한 패턴이 포함된 경우 (특수 심볼 허용: ^, =)\n",
    "        # 길이 제한 완화 (10 -> 15)\n",
    "        if (ticker.isdigit() or\n",
    "            any(pattern in ticker.upper() for pattern in invalid_patterns) or\n",
    "            len(ticker) > 15):\n",
    "            raise InvalidSymbolError(f\"'{ticker}'는 유효하지 않은 종목 심볼입니다.\")\n",
    "        \n",
    "        # 허용된 문자 확인: 영문, 숫자, ^, =, -, .\n",
    "        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789^=-.')\n",
    "        if not all(c in allowed_chars for c in ticker.upper()):\n",
    "            raise InvalidSymbolError(f\"'{ticker}'는 유효하지 않은 종목 심볼입니다.\")\n",
]

# 196-201 라인을 새로운 내용으로 교체
lines[196:202] = new_lines

# 파일 쓰기
with open('/home/kyj/source/backtest/backtest_be_fast/app/utils/data_fetcher.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("수정 완료!")
