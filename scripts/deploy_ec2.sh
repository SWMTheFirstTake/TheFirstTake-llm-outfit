#!/bin/bash

# EC2 배포 스크립트
# 이 스크립트는 EC2 인스턴스에서 직접 실행됩니다.

set -e

echo "🚀 TheFirstTake LLM Outfit API 배포를 시작합니다..."

# 환경 변수 설정
APP_NAME="llm-outfit-api"
CONTAINER_PORT=8000
HOST_PORT=8000
IMAGE_NAME="llm-outfit-api:latest"

# Docker 설치 확인 및 설치
if ! command -v docker &> /dev/null; then
    echo "📦 Docker를 설치하고 있습니다..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    sudo usermod -aG docker $USER
    echo "✅ Docker 설치 완료!"
fi

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 기존 컨테이너 중지 및 제거
echo "🔄 기존 컨테이너를 정리하고 있습니다..."
sudo docker stop $APP_NAME 2>/dev/null || true
sudo docker rm $APP_NAME 2>/dev/null || true

# 기존 이미지 제거 (선택사항)
echo "🧹 기존 이미지를 정리하고 있습니다..."
sudo docker rmi $IMAGE_NAME 2>/dev/null || true

# 새 이미지 빌드
echo "🔨 Docker 이미지를 빌드하고 있습니다..."
sudo docker build -t $IMAGE_NAME .

# 새 컨테이너 실행
echo "🚀 새 컨테이너를 실행하고 있습니다..."
sudo docker run -d \
    --name $APP_NAME \
    --restart unless-stopped \
    -p $HOST_PORT:$CONTAINER_PORT \
    -e ENVIRONMENT=production \
    $IMAGE_NAME

# 배포 확인
echo "✅ 배포가 완료되었습니다!"
echo "📍 서버 주소: http://$(curl -s ifconfig.me):$HOST_PORT"
echo "🔍 헬스 체크: http://$(curl -s ifconfig.me):$HOST_PORT/health"

# 컨테이너 상태 확인
echo "📊 컨테이너 상태:"
sudo docker ps | grep $APP_NAME

echo "🎉 배포가 성공적으로 완료되었습니다!" 