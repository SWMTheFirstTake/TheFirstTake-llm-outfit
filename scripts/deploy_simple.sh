#!/bin/bash

# Docker 없이 EC2에 직접 배포하는 스크립트

set -e

echo "🚀 TheFirstTake LLM Outfit API 배포를 시작합니다..."

# 환경 변수 설정
APP_DIR="/home/ubuntu/llm-outfit-api"
SERVICE_NAME="llm-outfit-api"
APP_NAME="llm-outfit-api"
CONTAINER_PORT=6020
HOST_PORT=6020

# 프로젝트 디렉토리 확인
if [ ! -d "$APP_DIR" ]; then
    echo "📁 프로젝트 디렉토리를 생성합니다..."
    mkdir -p $APP_DIR
    cd $APP_DIR
    git clone https://github.com/your-username/TheFirstTake-llm-outfit.git .
else
    cd $APP_DIR
    echo "📥 최신 코드를 가져옵니다..."
    git pull origin main
fi

# Python 가상환경 설정
if [ ! -d "venv" ]; then
    echo "📦 Python 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화 및 의존성 설치
echo "📦 의존성을 설치합니다..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 기존 서비스 중지
echo "🔄 기존 서비스를 중지합니다..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true

# systemd 서비스 파일 생성
echo "⚙️ 서비스 파일을 생성합니다..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=TheFirstTake LLM Outfit API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 6020
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 등록 및 시작
echo "🚀 서비스를 시작합니다..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# 배포 확인
echo "✅ 배포가 완료되었습니다!"
echo "📍 서버 주소: http://$(curl -s ifconfig.me):6020"
echo "🔍 헬스 체크: http://$(curl -s ifconfig.me):6020/health"

# 서비스 상태 확인
echo "📊 서비스 상태:"
sudo systemctl status $SERVICE_NAME --no-pager

echo "🎉 배포가 성공적으로 완료되었습니다!" 