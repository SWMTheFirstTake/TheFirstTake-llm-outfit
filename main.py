from fastapi import FastAPI
import logging
from api.fashion_routes import router
import os
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Fashion Expert API", version="2.0.0")

# 라우터 등록
app.include_router(router)

if __name__ == "__main__":
    load_dotenv()
    print("CLAUDE_API_KEY:", os.getenv("CLAUDE_API_KEY"))
    import uvicorn
    logger.info("🏃‍♂️ 패션 전문가 시스템 실행 중... 포트 6020")
    uvicorn.run("main:app", host="0.0.0.0", port=6020, reload=True) 