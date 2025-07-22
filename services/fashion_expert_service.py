import asyncio
import openai
import logging
import anthropic
from typing import List, Dict
from config import settings
from models.fashion_models import FashionExpertType, ExpertAnalysisRequest

logger = logging.getLogger(__name__)

class SimpleFashionExpertService:
    def __init__(self):
        # self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)  # 추가
        # 전문가별 특성 정의
        self.expert_profiles = {
            FashionExpertType.STYLE_ANALYST: {
                "role": "패션 스타일 분석 전문가",
                "expertise": "체형분석, 핏감분석, 실루엣",
                "focus": "사용자의 체형과 어울리는 스타일을 분석하고 핏감을 고려한 추천을 제공합니다.",
                "prompt_template": "이전 전문가의 의견을 참고하되, 당신의 전문 분야인 체형분석과 핏감 관점에서 독립적으로 평가하세요. 동의할 수도 있고, 다른 관점에서 우려사항이나 대안을 제시할 수도 있습니다. 당신의 전문적 판단을 솔직하게 표현하고, 체형과 실루엣 관점에서 어울리는 스타일을 추천해주세요. 반드시 구체적인 색상(네이비, 베이지, 화이트, 차콜, 블랙, 그레이 등), 소재(코튼, 린넨, 울, 데님 등), 핏(슬림핏, 레귤러핏, 오버핏 등)을 포함해서 추천해주세요. 간결하고 자연스러운 문장으로 추천하고, 마지막에 조합에 대한 한 줄 평을 추가하세요. 성별은 모르겠으면 물어보거나, 20대 남자로 가정하세요."
            },
            FashionExpertType.TREND_EXPERT: {
                "role": "패션 트렌드 전문가",
                "expertise": "최신트렌드, 셀럽스타일",
                "focus": "최신 패션 트렌드, 인플루언서 스타일을 반영한 추천을 제공합니다.",
                "prompt_template": "이전 전문가의 의견을 고려하되, 트렌드 전문가로서 당신만의 관점을 유지하세요. 현재 트렌드와 맞지 않거나 오버된 스타일이라면 솔직하게 지적하고, 트렌디한 대안을 제시하세요. 때로는 이전 의견에 동의하지 않을 수도 있습니다. 현재 트렌드와 셀럽 스타일을 기준으로 한 당신의 솔직한 평가와 추천을 해주세요. 반드시 구체적인 색상(라벤더, 세이지 그린, 테라코타, 네이비, 베이지, 화이트 등), 소재(코튼, 린넨, 울, 데님 등), 핏(슬림핏, 레귤러핏, 오버핏 등)을 포함해서 추천해주세요. 간결하고 자연스러운 문장으로 추천하고, 마지막에 조합에 대한 한 줄 평을 추가하세요."
            },
            # FashionExpertType.BUDGET_MANAGER: {
            #     "role": "패션 예산 관리 전문가", 
            #     "expertise": "가격비교, 가성비, 투자가치",
            #     "focus": "예산 대비 최적의 가성비와 장기적 투자가치를 고려한 현실적인 추천을 제공합니다.",
            #     "prompt_template": "예산을 고려하여 가성비 좋고 투자가치가 높은 실용적인 옷을 추천해주세요."
            # },
            FashionExpertType.COLOR_EXPERT: {
                "role": "퍼스널 컬러 전문가",
                "expertise": "퍼스널컬러, 색상조합, 톤온톤", 
                "focus": "개인의 피부톤과 어울리는 색상 분석과 조화로운 컬러 조합을 제안합니다.",
                "prompt_template": "이전 전문가들의 의견을 참고하되, 컬러 전문가로서 당신의 독립적인 판단을 유지하세요. 색상 조합이 부적절하거나 퍼스널 컬러와 맞지 않는다면 솔직하게 지적하고, 더 나은 색상 대안을 제시하세요. 때로는 이전 의견에 동의하지 않을 수도 있습니다. 퍼스널 컬러와 색상 조합 관점에서 당신의 솔직한 평가와 추천을 해주세요. 반드시 구체적인 색상(네이비, 베이지, 화이트, 차콜, 블랙, 그레이, 라벤더, 세이지 그린 등), 소재(코튼, 린넨, 울, 데님 등), 핏(슬림핏, 레귤러핏, 오버핏 등)을 포함해서 추천해주세요. 간결하고 자연스러운 문장으로 추천하고, 마지막에 조합에 대한 한 줄 평을 추가하세요. 성별과 피부톤을 사용자가 알려주지 않은 경우에는 일반적인 20대 남자로 가정하고, 사용자에게 물어보세요."
            },
            # FashionExpertType.TPO_EXPERT: {
            #     "role": "TPO 상황별 패션 전문가",
            #     "expertise": "상황분석, 드레스코드, 예의범절",
            #     "focus": "시간, 장소, 상황에 맞는 적절한 드레스코드와 예의를 고려한 패션을 제안합니다.",
            #     "prompt_template": "상황과 장소에 맞는 적절한 드레스코드를 고려하여 예의에 맞는 옷을 추천해주세요."
            # },
            FashionExpertType.FITTING_COORDINATOR: {
                "role": "가상 피팅 코디네이터",
                "expertise": "피팅연동, 결과분석, 대안제시",
                "focus": "모든 전문가의 의견을 종합하여 최종 코디네이션을 완성합니다.",
                "prompt_template": "앞선 전문가들의 다양한 의견을 종합하여 최종 평가를 내려주세요. 모든 의견이 일치하지 않을 수 있으니, 각 전문가의 관점을 고려하면서도 최종적으로 가장 적합한 코디네이션을 제안해주세요. 의견이 충돌하는 부분이 있다면 그 이유와 함께 최종 판단을 설명해주세요. 최종 추천에서는 반드시 구체적인 색상(네이비, 베이지, 화이트, 차콜, 블랙, 그레이 등), 소재(코튼, 린넨, 울, 데님 등), 핏(슬림핏, 레귤러핏, 오버핏 등)을 포함해서 추천해주세요. 간결하고 자연스러운 문장으로 추천하고, 마지막에 조합에 대한 한 줄 평을 추가하세요."
            }
        }
    
    async def get_single_expert_analysis(self, request: ExpertAnalysisRequest):
        """단일 전문가 분석"""
        expert_profile = self.expert_profiles[request.expert_type]
        
        # 전문가별 프롬프트 구성
        context_parts = [f"사용자 요청: {request.user_input}"]
        
        if request.user_profile:
            context_parts.append(f"사용자 정보: {request.user_profile}")
        
        if request.context_info:
            context_parts.append(f"상황 정보: {request.context_info}")
        
        context_parts.append(f"\n{expert_profile['role']}으로서 {expert_profile['prompt_template']}")
        
        # 구체적 형식 강조
        context_parts.append("\n⚠️ 중요: 추천할 때 반드시 '색상+소재+핏+아이템명' 형식으로 구체적으로 표현하세요.")
        context_parts.append("간결하고 자연스러운 문장으로 추천하고, 마지막에 조합에 대한 한 줄 평을 추가하세요.")
        context_parts.append("예시: '네이비 코튼 슬림핏 셔츠와 베이지 울 레귤러핏 팬츠를 추천드려요. 깔끔하면서도 세련된 느낌을 줄 수 있어요.'")
        context_parts.append("추상적인 표현(예: '슬림핏 셔츠', '다크 진')은 사용하지 마세요.")
        
        expert_prompt = "\n\n".join(context_parts)
        
        # OpenAI 호출
        try:
            system_prompt = f"""당신은 {expert_profile['role']}입니다. {expert_profile['focus']} 전문 영역: {expert_profile['expertise']}

중요한 원칙:
1. 당신의 전문 분야에 대한 독립적인 판단을 유지하세요
2. 이전 전문가의 의견에 무조건 동의하지 마세요
3. 당신의 관점에서 문제점이나 우려사항이 있다면 솔직하게 표현하세요
4. 때로는 이전 의견과 다른 대안을 제시하는 것이 좋습니다
5. 당신의 전문성을 바탕으로 한 솔직하고 건설적인 피드백을 제공하세요

구체적 정보 포함 필수:
- 반드시 색상을 명시하세요 (예: 네이비, 베이지, 화이트, 차콜, 블랙, 그레이 등)
- 소재를 명시하세요 (예: 코튼, 린넨, 울, 데님, 실크 등)
- 핏을 명시하세요 (예: 슬림핏, 레귤러핏, 오버핏, 루즈핏 등)
- 구체적인 아이템명을 사용하세요 (예: "슬림핏 셔츠" 대신 "네이비 코튼 슬림핏 셔츠")

응답 형식:
- 간결하고 자연스러운 문장으로 추천하세요
- "색상+소재+핏+아이템명" 형식으로 구체적으로 표현
- 마지막에 조합에 대한 한 줄 평을 추가하세요
- 예시: "네이비 코튼 슬림핏 셔츠와 베이지 울 레귤러핏 팬츠를 추천드려요. 깔끔하면서도 세련된 느낌을 줄 수 있어요."

추상적인 표현 금지:
- "예쁜 옷", "멋진 스타일" 같은 추상적 표현 사용 금지
- 반드시 구체적인 색상, 소재, 핏 정보를 포함해야 합니다"""
            
            response = await self._call_openai_async(
                system_prompt,
                expert_prompt
            )
            
            return {
                "expert_type": request.expert_type.value,
                "expert_role": expert_profile["role"],
                "analysis": response,
                "expertise_areas": expert_profile["expertise"]
            }
            
        except Exception as e:
            logger.error(f"전문가 분석 실패 - {request.expert_type}: {e}")
            raise e
    
    async def get_expert_chain_analysis(self, request):
        """전문가 체인 분석"""
        expert_results = []
        accumulated_insights = []
        
        for expert_type in request.expert_sequence or []:
            # 이전 전문가들의 결과를 컨텍스트에 포함
            current_context = request.context_info or {}
            if accumulated_insights:
                current_context["previous_expert_insights"] = accumulated_insights[-3:]  # 최근 3개만
            
            expert_request = ExpertAnalysisRequest(
                user_input=request.user_input,
                room_id=request.room_id,
                expert_type=expert_type,
                user_profile=request.user_profile,
                context_info=current_context
            )
            
            expert_result = await self.get_single_expert_analysis(expert_request)
            expert_results.append(expert_result)
            
            # 다음 전문가를 위한 인사이트 누적
            accumulated_insights.append({
                "expert": expert_type.value,
                "key_point": expert_result["analysis"][:100] + "..."  # 요약만
            })
        
        # 최종 종합
        return {
            "expert_analyses": expert_results,
            # "expert_count": len(expert_results),
            # "comprehensive_recommendation": self._synthesize_results(expert_results),
            # "collaboration_flow": accumulated_insights
        }
    
    def _synthesize_results(self, expert_results: List[Dict]) -> str:
        """전문가 결과 종합"""
        synthesis = "===== 종합 패션 추천 =====\n\n"
        
        for result in expert_results:
            synthesis += f"🔹 {result['expert_role']}: {result['analysis'][:150]}...\n\n"
        
        synthesis += "📋 최종 추천: 모든 전문가의 조언을 종합하여 가장 적합한 단 하나의 스타일을 선택하시기 바랍니다. 대안 없이."
        
        return synthesis
    
    async def _call_openai_async(self, system_prompt: str, user_prompt: str) -> str:
        """비동기 OpenAI 호출"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._call_openai_sync,
            system_prompt,
            user_prompt
        )
        return response
    
    def _call_openai_sync(self, system_prompt: str, user_prompt: str) -> str:
        # """동기 OpenAI 호출"""
        # response = self.client.chat.completions.create(
        #     model=settings.LLM_MODEL_NAME,
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ],
        #     max_tokens=settings.LLM_MAX_TOKENS,
        #     temperature=settings.LLM_TEMPERATURE
        # )
        # content = response.choices[0].message.content
        # if content is None:
        #     return "응답을 생성할 수 없습니다."
        # return content 
        """Claude API 호출로 변경"""
        response = self.client.messages.create(
            model=settings.LLM_MODEL_NAME,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            system=system_prompt,  # Claude는 system 파라미터 사용
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        content = response.content[0].text  # Claude 응답 구조
        if content is None:
            return "응답을 생성할 수 없습니다."
        return content
        