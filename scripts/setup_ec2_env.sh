#!/bin/bash

# EC2 환경변수 설정 스크립트

echo "🔧 EC2 환경변수를 설정합니다..."

# 프로젝트 디렉토리
APP_DIR="/home/ubuntu/llm-outfit-api"

# .env 파일 생성
cat > $APP_DIR/.env <<EOF
# 프로덕션 환경 설정
ENVIRONMENT=production
DEBUG=False
LLM_API_HOST=0.0.0.0
LLM_API_PORT=6020
LOG_LEVEL=INFO

# 데이터베이스 설정 (필요시)
# DATABASE_URL=postgresql://user:password@localhost/dbname

# 외부 API 키 (필요시)
OPENAI_API_KEY=your_production_api_key_here

# LLM 관련 설정
LLM_MODEL_NAME=gpt-4
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.5

# LLM Outfit 전용 설정
LLM_OUTFIT_APP_NAME=llm-outfit-api
LLM_OUTFIT_SERVICE_NAME=llm-outfit-api
EOF

echo "✅ 환경변수 파일이 생성되었습니다: $APP_DIR/.env"
echo "📝 필요한 API 키나 데이터베이스 설정을 추가로 편집하세요." 