from pydantic import BaseModel
from typing import TypeVar, Generic, Optional
T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    status: str = "success"
    message: str = "Operation was successful."
    data: Optional[T]  # 제너릭 타입으로 데이터 정의