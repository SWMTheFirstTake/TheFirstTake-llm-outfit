from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from api.fashion_routes import router
import os
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Fashion Expert API", version="2.0.0")

# 서버 시작 시 인덱스 상태 확인 및 복구
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Redis 인덱스 상태 확인 및 자동 복구"""
    logger.info("🔍 서버 시작 - Redis 인덱스 상태 확인 중...")
    try:
        from services.fashion_index_service import fashion_index_service
        
        # 백그라운드에서 인덱스 상태 확인 및 복구 (서버 시작 지연 방지)
        import threading
        def background_index_check():
            try:
                logger.info("🔨 백그라운드에서 인덱스 상태 확인 시작...")
                fashion_index_service._check_and_recover_indexes()
                logger.info("✅ 백그라운드 인덱스 확인 완료")
            except Exception as e:
                logger.error(f"❌ 백그라운드 인덱스 확인 실패: {e}")
        
        # 데몬 스레드로 실행 (메인 프로세스 종료 시 자동 종료)
        index_thread = threading.Thread(target=background_index_check, daemon=True)
        index_thread.start()
        logger.info("🚀 서버 시작 완료 (인덱스 확인은 백그라운드에서 진행 중)")
        
    except Exception as e:
        logger.error(f"❌ 인덱스 복구 시작 실패: {e}")
        # 실패해도 서버는 계속 시작

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 라우터 등록
app.include_router(router)

if __name__ == "__main__":
    load_dotenv()
    print("CLAUDE_API_KEY:", os.getenv("CLAUDE_API_KEY"))
    import uvicorn
    logger.info("🏃‍♂️ 패션 전문가 시스템 실행 중... 포트 6020")
    uvicorn.run("main:app", host="0.0.0.0", port=6020, reload=True) 