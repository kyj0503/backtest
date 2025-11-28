#!/usr/bin/env python3
"""파일 수정 스크립트 - 197-202번 라인만 정확하게 수정"""

filepath = '/home/kyj/source/backtest/backtest_be_fast/app/utils/data_fetcher.py'

# 파일 읽기
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 기존 197-202번 라인(0-indexed: 196-201)을 새로운 내용으로 교체
# 기존:
# 197:         # 숫자로만 구성되거나 무효한 패턴이 포함된 경우
# 198:         if (ticker.isdigit() or
# 199:             any(pattern in ticker.upper() for pattern in invalid_patterns) or
# 200:             len(ticker) > 10 or
# 201:             not ticker.replace('.', '').replace('-', '').isalnum()):
# 202:             raise InvalidSymbolError(f"'{ticker}'는 유효하지 않은 종목 심볼입니다.")

new_content = """        # 숫자로만 구성되거나 무효한 패턴이 포함된 경우 (특수 심볼 허용: ^, =)
        if (ticker.isdigit() or
            any(pattern in ticker.upper() for pattern in invalid_patterns) or
            len(ticker) > 15):  # 길이 제한 완화
            raise InvalidSymbolError(f"'{ticker}'는 유효하지 않은 좁목 심볼입니다.")
        
        # 허용된 문자 확인: 영문, 숫자, ^, =, -, .
        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789^=-.')
        if not all(c in allowed_chars for c in ticker.upper()):
            raise InvalidSymbolError(f"'{ticker}'는 유효하지 않은 종목 심볼입니다.")
"""

# 196-201 (0-indexed) 교체
lines[196:202] = [new_content]

# 파일 쓰기
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✓ 파일 수정 완료!")
print(f"197-202번 라인을 {len(new_content.splitlines())} 라인으로 교체했습니다.")
