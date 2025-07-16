from fastapi import FastAPI
from pydantic import BaseModel
from services.gpt_service import ask_gpt
from typing import Generic, TypeVar, Optional, List
from pydantic.generics import GenericModel
import re

# 공통 응답 모델 정의
T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    status: str = "success"
    message: str = "Operation was successful."
    data: Optional[T]  # 제너릭 타입으로 데이터 정의

# 실제 응답에 들어갈 데이터 모델
class AskResponseData(BaseModel):
    question: str
    options: List[str]  # 응답을 리스트로 저장

# 실제 FastAPI 애플리케이션 설정
app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

# 질문과 응답을 분리하는 함수
def split_question_and_answers(generated_text: str):
    # 전체 줄을 분리
    lines = generated_text.strip().splitlines()

    question = ""
    options = []

    # 1. 먼저 질문 찾기 (Q. 로 시작하는 줄)
    for line in lines:
        if line.strip().startswith("Q."):
            question = line.strip().replace("Q.", "").strip()
            break  # 첫 번째 질문만 추출

    # 2. 그 외의 줄 중에서 A., B., C. 등으로 시작하는 줄을 답변으로 추출
    for line in lines:
        line = line.strip()
        match = re.match(r"^[A-PR-Z]\.\s*(.*)", line)  # Q 제외
        if match:
            options.append(match.group(1).strip())

    return question, options
    
@app.post("/api/ask")
def ask(request: PromptRequest):
    generated_text = ask_gpt(request.prompt)
    return ResponseModel(data=generated_text)

@app.get("/api/test")
def test():
    return {"message": "Hello, World!"}