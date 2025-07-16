#!/usr/bin/env python3
"""
로컬 개발 환경에서 FastAPI 서버를 시작하는 스크립트
"""

import subprocess
import sys
import os

def install_requirements():
    """의존성 패키지 설치"""
    print("📦 의존성 패키지를 설치하고 있습니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 의존성 설치 완료!")
    except subprocess.CalledProcessError:
        print("❌ 의존성 설치 실패!")
        return False
    return True

def start_server():
    """FastAPI 서버 시작"""
    print("🚀 FastAPI 서버를 시작합니다...")
    print("📍 서버 주소: http://localhost:6020")
    print("📚 API 문서: http://localhost:6020/docs")
    print("🔍 헬스 체크: http://localhost:6020/health")
    print("\n서버를 중지하려면 Ctrl+C를 누르세요.\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "6020", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 서버가 중지되었습니다.")

if __name__ == "__main__":
    print("🎯 TheFirstTake LLM Outfit API - 로컬 개발 서버")
    print("=" * 50)
    
    if install_requirements():
        start_server()
    else:
        sys.exit(1) 