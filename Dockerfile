FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치 (curl은 헬스체크용)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치 (레이어 캐시 최적화)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 비루트 사용자 생성 및 권한 설정
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 포트 노출
EXPOSE 6020

# 애플리케이션 실행 (workers 수는 환경변수로 조정 가능: UVICORN_WORKERS)
ENV UVICORN_WORKERS=2
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6020", "--workers", "2"]