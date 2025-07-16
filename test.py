# import openai
# import os
# from typing import Any
# # from dotenv import load_dotenv

# # load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# models: Any = openai.Model.list()

# # 모델 ID 목록 출력
# for model in models['data']:
#     print(model['id'])
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

models = client.models.list()
for model in models.data:
    print(model.id)