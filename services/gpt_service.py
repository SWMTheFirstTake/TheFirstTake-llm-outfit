import openai
from config import settings
import logging

# 로깅 설정
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# OpenAI 클라이언트 설정
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def ask_gpt(prompt: str) -> str:
    """
    GPT 모델에 질문을 하고 응답을 받는 함수
    
    Args:
        prompt (str): 사용자 질문
        
    Returns:
        str: GPT 응답
    """
    try:
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API 키가 설정되지 않았습니다.")
            return "OpenAI API 키가 설정되지 않았습니다. 환경변수 OPENAI_API_KEY를 설정해주세요."
        
        response = client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "당신은 의상 추천 전문가입니다. 사용자의 질문에 친근하고 도움이 되는 답변을 해주세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE
        )
        
        return response.choices[0].message.content
        
    except openai.AuthenticationError:
        logger.error("OpenAI API 인증 실패")
        return "OpenAI API 인증에 실패했습니다. API 키를 확인해주세요."
    except openai.RateLimitError:
        logger.error("OpenAI API 요청 한도 초과")
        return "API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
    except Exception as e:
        logger.error(f"OpenAI API 호출 중 오류 발생: {str(e)}")
        return f"오류가 발생했습니다: {str(e)}"

def get_available_models():
    """
    사용 가능한 OpenAI 모델 목록을 가져오는 함수
    
    Returns:
        list: 모델 목록
    """
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        logger.error(f"모델 목록 조회 중 오류 발생: {str(e)}")
        return []
