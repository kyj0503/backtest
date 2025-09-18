# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*


# Python 의존성 설치 (uv 기반 유지)
COPY requirements.txt .
# VENV 위치를 소스 밖(/opt/venv)에 두어 바인드 마운트로 덮어지지 않게 함
ENV VENV_DIR=/opt/venv
RUN python3 -m venv ${VENV_DIR}
ENV PATH="${VENV_DIR}/bin:$PATH"

# (옵션) uv 설치: keep for compatibility, but use pip in venv
RUN curl -Ls https://astral.sh/uv/install.sh | sh \
    && cp /root/.local/bin/uv /usr/local/bin/uv || true

# requirements 설치 (venv 내부 pip 사용)
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app ./app
COPY run_server.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 빌드 인자 및 메타데이터
ARG IMAGE_TAG=latest

# 환경변수로 설정
ENV IMAGE_TAG=${IMAGE_TAG}
ENV IMAGE_NAME=backtest-backend

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 서버 실행
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
