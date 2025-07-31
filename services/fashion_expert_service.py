import asyncio
import openai
import logging
import anthropic
import json
import os
from typing import List, Dict, Optional
from config import settings
from models.fashion_models import FashionExpertType, ExpertAnalysisRequest

logger = logging.getLogger(__name__)

class SimpleFashionExpertService:
    def __init__(self, api_key: str):
        # self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.client = anthropic.Anthropic(api_key=api_key)
        # API 키 상태 확인
        print(f"🔍 CLAUDE_API_KEY 상태: {'설정됨' if api_key else '설정되지 않음'}")
        print(f"🔍 CLAUDE_API_KEY 길이: {len(api_key) if api_key else 0}")
        print(f"🔍 CLAUDE_API_KEY 앞 10자: {api_key[:10] if api_key else 'None'}")
        
        # if not settings.CLAUDE_API_KEY:
        #     raise ValueError("CLAUDE_API_KEY가 설정되지 않았습니다. 환경변수를 확인해주세요.")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY가 설정되지 않았습니다. 환경변수를 확인해주세요.")
        
        # 패션 참고 데이터 로드
        print("🚀 패션 참고 데이터 로딩 시작...")
        self.fashion_reference_data = self._load_fashion_reference_data()
        print(f"✅ 패션 참고 데이터 로딩 완료!")
        print(f"   - 패션 아이템: {len(self.fashion_reference_data['fashion_items'])}개")
        print(f"   - 아웃핏 조합: {len(self.fashion_reference_data['outfit_combinations'])}개")
        print(f"   - 컬러 추천: {len(self.fashion_reference_data['color_recommendations'])}개")
        print(f"   - 스타일링 팁: {len(self.fashion_reference_data['styling_tips'])}개")
        
        # 전문가별 특성 정의
        self.expert_profiles = {
            FashionExpertType.STYLE_ANALYST: {
                "role": "패션 스타일 분석 전문가",
                "expertise": "체형분석, 핏감분석, 실루엣",
                "focus": "사용자의 체형과 어울리는 스타일을 분석하고 핏감을 고려한 추천을 제공합니다.",
                # 개선된 프롬프트 - 자연스러운 대화 스타일
                "prompt_template": """당신은 스타일 분석가입니다. 분석된 옷 조합 정보와 스타일링 방법을 바탕으로 자연스럽게 대화해주세요.

**대화 스타일:**
- 친구처럼 편안하고 자연스럽게 대화
- 분석된 JSON 데이터의 실제 정보를 자연스럽게 언급
- 다양한 표현과 어조 사용 (감탄, 걱정, 제안, 설명 등)
- 상황에 따라 다른 반응 (칭찬, 조언, 질문 등)

**JSON 데이터 활용:**
- top: 상의 정보 (item, color, fit, material)
- bottom: 하의 정보 (item, color, fit, material)  
- shoes: 신발 정보 (item, color, style)
- accessories: 액세서리 정보
- styling_methods: 스타일링 방법 (top_wearing_method, tuck_degree, fit_details 등)

**대화 예시 (다양한 스타일):**
- "{top_color} {top_item} + {bottom_color} {bottom_item} 조합이 나쁘지 않아. {styling_points} 포인트가 괜찮아."
- "{tuck_degree} 스타일링이 좀 아쉽다. {silhouette_balance}를 위해 다른 방법은 어떨까?"
- "{top_color} {top_item}이 괜찮네. {fit_details}라서 체형이 좀 보완될 거야. {bottom_color} {bottom_item}도 잘 어울려."
- "체형에 {top_item}이 적당해. {fit_details}라서 날씬해 보일 거야. {bottom_color} {bottom_item} 조합이 나쁘지 않아."

**핵심 규칙:**
1. 반드시 JSON 데이터의 실제 정보를 사용하되, 자연스럽게 녹여내기
2. 다양한 감정과 어조로 대화 (기쁨, 걱정, 확신, 제안 등)
3. 상황에 맞는 반응 (칭찬, 조언, 질문, 설명)
4. 2-3문장으로 간결하게, 하지만 다양하게"""
            },
            FashionExpertType.TREND_EXPERT: {
                "role": "패션 트렌드 전문가",
                "expertise": "최신트렌드, 셀럽스타일",
                "focus": "최신 패션 트렌드, 인플루언서 스타일을 반영한 추천을 제공합니다.",
                # 개선된 프롬프트 - 자연스러운 대화 스타일
                "prompt_template": """당신은 트렌드 전문가입니다. 분석된 옷 조합 정보와 스타일링 방법을 바탕으로 자연스럽게 대화해주세요.

**대화 스타일:**
- 트렌디하고 활기찬 어조로 대화
- 분석된 JSON 데이터의 실제 정보를 자연스럽게 언급
- 다양한 표현과 어조 사용 (감탄, 놀람, 확신, 제안 등)
- 상황에 따라 다른 반응 (칭찬, 조언, 질문 등)

**JSON 데이터 활용:**
- top: 상의 정보 (item, color, fit, material)
- bottom: 하의 정보 (item, color, fit, material)  
- shoes: 신발 정보 (item, color, style)
- accessories: 액세서리 정보
- styling_methods: 스타일링 방법 (top_wearing_method, tuck_degree, fit_details 등)

**대화 예시 (다양한 스타일):**
- "{top_color} {top_item} + {bottom_color} {bottom_item} 조합이 요즘 유행이야. {silhouette_balance}가 괜찮아."
- "{styling_points} 스타일링이 좀 올드해. 요즘은 다른 방법이 더 인기 있어."
- "이 조합 인스타에서 자주 보여. {fit_details}가 트렌디해. {top_color} {top_item} + {bottom_color} {bottom_item}이 핫해."
- "{top_item} 요즘 많이 입어. {top_color} 컬러가 이번 시즌에 괜찮아. {bottom_color} {bottom_item}도 트렌디해."

**핵심 규칙:**
1. 반드시 JSON 데이터의 실제 정보를 사용하되, 자연스럽게 녹여내기
2. 트렌디하고 활기찬 어조로 대화
3. 상황에 맞는 반응 (칭찬, 조언, 질문, 설명)
4. 2-3문장으로 간결하게, 하지만 다양하게"""
            },
            FashionExpertType.COLOR_EXPERT: {
                "role": "퍼스널 컬러 전문가",
                "expertise": "퍼스널컬러, 색상조합, 톤온톤", 
                "focus": "개인의 피부톤과 어울리는 색상 분석과 조화로운 컬러 조합을 제안합니다.",
                # 개선된 프롬프트 - 자연스러운 대화 스타일
                "prompt_template": """당신은 컬러 전문가입니다. 분석된 옷 조합 정보와 스타일링 방법을 바탕으로 자연스럽게 대화해주세요.

**대화 스타일:**
- 색상에 대한 감탄과 전문성을 담은 대화
- 분석된 JSON 데이터의 실제 정보를 자연스럽게 언급
- 다양한 표현과 어조 사용 (감탄, 걱정, 확신, 제안 등)
- 상황에 따라 다른 반응 (칭찬, 조언, 질문 등)

**JSON 데이터 활용:**
- top: 상의 정보 (item, color, fit, material)
- bottom: 하의 정보 (item, color, fit, material)  
- shoes: 신발 정보 (item, color, style)
- accessories: 액세서리 정보
- styling_methods: 스타일링 방법 (top_wearing_method, tuck_degree, fit_details 등)

**대화 예시 (다양한 스타일):**
- "{top_color} {top_item} + {bottom_color} {bottom_item} 조합이 괜찮아. 톤온톤이 나쁘지 않아."
- "색상 조합이 좀 어색해. {top_color} 대신 다른 색상은 어떨까?"
- "퍼스널 컬러랑 어울려. {top_color}가 피부톤을 밝게 해줘. {top_color} {top_item} + {bottom_color} {bottom_item} 조합이 좋아."
- "색상 밸런스가 괜찮아. {styling_points} 포인트도 색상과 잘 맞아."

**핵심 규칙:**
1. 반드시 JSON 데이터의 실제 정보를 사용하되, 자연스럽게 녹여내기
2. 색상에 대한 전문성과 감탄을 담은 대화
3. 상황에 맞는 반응 (칭찬, 조언, 질문, 설명)
4. 2-3문장으로 간결하게, 하지만 다양하게"""
            },
            FashionExpertType.FITTING_COORDINATOR: {
                "role": "가상 피팅 코디네이터",
                "expertise": "피팅연동, 결과분석, 대안제시",
                "focus": "모든 전문가의 의견을 종합하여 최종 코디네이션을 완성합니다.",
                # 개선된 프롬프트 - 자연스러운 대화 스타일
                "prompt_template": """당신은 피팅 코디네이터입니다. 분석된 옷 조합 정보와 스타일링 방법을 바탕으로 자연스럽게 대화해주세요.

**대화 스타일:**
- 종합적이고 균형잡힌 관점으로 대화
- 분석된 JSON 데이터의 실제 정보를 자연스럽게 언급
- 다양한 표현과 어조 사용 (감탄, 걱정, 확신, 제안 등)
- 상황에 따라 다른 반응 (칭찬, 조언, 질문 등)

**JSON 데이터 활용:**
- top: 상의 정보 (item, color, fit, material)
- bottom: 하의 정보 (item, color, fit, material)  
- shoes: 신발 정보 (item, color, style)
- accessories: 액세서리 정보
- styling_methods: 스타일링 방법 (top_wearing_method, tuck_degree, fit_details 등)

**대화 예시 (다양한 스타일):**
- "{top_color} {top_item} + {bottom_color} {bottom_item} 조합이 괜찮아. {silhouette_balance}가 나쁘지 않아."
- "전체적으로는 좋은데 {styling_points} 부분을 조금 바꾸면 더 나을 것 같아."
- "이 룩 괜찮아. {fit_details}와 {tuck_degree}가 균형잡혀 있어. {top_color} {top_item} + {bottom_color} {bottom_item} 조합이 좋아."
- "피팅 관점에서는 괜찮아. {top_color} {top_item} + {bottom_color} {bottom_item} 조합도 나쁘지 않아."

**핵심 규칙:**
1. 반드시 JSON 데이터의 실제 정보를 사용하되, 자연스럽게 녹여내기
2. 종합적이고 균형잡힌 관점으로 대화
3. 상황에 맞는 반응 (칭찬, 조언, 질문, 설명)
4. 2-3문장으로 간결하게, 하지만 다양하게"""
            }
        }
    
    def _load_fashion_reference_data(self) -> Dict:
        """패션 참고 데이터 로드"""
        reference_data = {
            "fashion_items": [],
            "outfit_combinations": [],
            "styling_tips": [],
            "color_recommendations": [],
            "seasonal_advice": []
        }
        
        # fashion_summary 디렉토리 경로 (절대 경로 사용)
        pipeline_dir = r"C:\fashion_summary"
        
        # print(f"🔍 JSON 파일 검색 중: {pipeline_dir}")
        # print(f"🔍 디렉토리 존재 여부: {os.path.exists(pipeline_dir)}")
        
        try:
            # print(f"🔍 JSON 파일 검색 중: {pipeline_dir}")
            
            # 디렉토리 존재 확인
            if not os.path.exists(pipeline_dir):
                print(f"❌ 디렉토리가 존재하지 않음: {pipeline_dir}")
                # JSON 파일이 없으면 빈 데이터 반환
                print(f"⚠️ JSON 파일을 찾을 수 없어 빈 데이터를 반환합니다.")
                return reference_data
            
            # JSON 파일들 로드
            json_files_found = 0
            successful_loads = 0
            for filename in os.listdir(pipeline_dir):
                if filename.endswith('.json') and filename.startswith('fashion_extract_'):
                    json_files_found += 1
                    file_path = os.path.join(pipeline_dir, filename)
                    # print(f"📄 JSON 파일 로드 중: {filename}")
                    
                    # 여러 인코딩으로 시도
                    encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
                    data = None
                    
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                data = json.load(f)
                                break
                        except:
                            continue
                    
                    if not data:
                        print(f"   ❌ 모든 인코딩으로 읽기 실패: {filename}")
                        continue
                    
                    if 'fashion_data' in data:
                        fashion_data = data['fashion_data']
                        successful_loads += 1
                        # print(f"   📂 파일 '{filename}'에서 데이터 로드 중...")
                        
                        # 패션 아이템들 추가
                        if 'fashion_items' in fashion_data:
                            reference_data['fashion_items'].extend(fashion_data['fashion_items'])
                            # print(f"   ✅ 패션 아이템 {len(fashion_data['fashion_items'])}개 추가")
                            # for i, item in enumerate(fashion_data['fashion_items'][:3], 1):  # 처음 3개만 출력
                            #     print(f"      {i}. {item.get('item', 'N/A')}")
                        
                        # 아웃핏 조합들 추가
                        if 'outfit_combinations' in fashion_data:
                            reference_data['outfit_combinations'].extend(fashion_data['outfit_combinations'])
                            # print(f"   ✅ 아웃핏 조합 {len(fashion_data['outfit_combinations'])}개 추가")
                            # for i, combo in enumerate(fashion_data['outfit_combinations'][:3], 1):  # 처음 3개만 출력
                            #     print(f"      {i}. {combo.get('combination', 'N/A')} - {combo.get('items', [])}")
                        
                        # 스타일링 팁들 추가
                        if 'styling_tips' in fashion_data:
                            reference_data['styling_tips'].extend(fashion_data['styling_tips'])
                            # print(f"   ✅ 스타일링 팁 {len(fashion_data['styling_tips'])}개 추가")
                            # for i, tip in enumerate(fashion_data['styling_tips'][:2], 1):  # 처음 2개만 출력
                            #     print(f"      {i}. {tip[:50]}...")
                        
                        # 컬러 추천들 추가
                        if 'color_recommendations' in fashion_data:
                            reference_data['color_recommendations'].extend(fashion_data['color_recommendations'])
                            # print(f"   ✅ 컬러 추천 {len(fashion_data['color_recommendations'])}개 추가")
                            # for i, color in enumerate(fashion_data['color_recommendations'][:3], 1):  # 처음 3개만 출력
                            #     print(f"      {i}. {color.get('color', 'N/A')} - {color.get('description', 'N/A')[:30]}...")
                        
                        # 계절별 조언 추가
                        if 'seasonal_advice' in fashion_data:
                            reference_data['seasonal_advice'].append(fashion_data['seasonal_advice'])
                            # print(f"   ✅ 계절 조언 추가")
                            # print(f"      📝 {fashion_data['seasonal_advice'][:50]}...")
                    else:
                        print(f"   ⚠️ fashion_data 키가 없음: {filename}")
            
            if json_files_found == 0:
                print(f"❌ fashion_extract_*.json 파일을 찾을 수 없음")
                # JSON 파일이 없으면 빈 데이터 반환
                print(f"⚠️ JSON 파일을 찾을 수 없어 빈 데이터를 반환합니다.")
                return reference_data
            
            print(f"🎯 JSON 파일 {json_files_found}개 발견, {successful_loads}개 성공적으로 로드됨")
            
            # print(f"📚 패션 참고 데이터 로드 완료:")
            # print(f"   - 패션 아이템: {len(reference_data['fashion_items'])}개")
            # print(f"   - 아웃핏 조합: {len(reference_data['outfit_combinations'])}개")
            # print(f"   - 스타일링 팁: {len(reference_data['styling_tips'])}개")
            # print(f"   - 컬러 추천: {len(reference_data['color_recommendations'])}개")
            # print(f"   - 계절별 조언: {len(reference_data['seasonal_advice'])}개")
            
            # 실제 데이터 샘플 출력 (디버깅용)
            # if reference_data['outfit_combinations']:
            #     print(f"   🎯 첫 번째 아웃핏 조합: {reference_data['outfit_combinations'][0]}")
            # if reference_data['fashion_items']:
            #     print(f"   👕 첫 번째 패션 아이템: {reference_data['fashion_items'][0]}")
            # if reference_data['color_recommendations']:
            #     print(f"   🎨 첫 번째 컬러 추천: {reference_data['color_recommendations'][0]}")
            
        except Exception as e:
            print(f"⚠️ 패션 참고 데이터 로드 실패: {e}")
            # 오류 발생 시 빈 데이터 반환
            print(f"⚠️ 오류로 인해 빈 데이터를 반환합니다.")
        
        return reference_data
    
    def _get_relevant_reference_data(self, user_input: str) -> str:
        """사용자 입력과 관련된 참고 데이터 추출"""
        relevant_data = []
        
        # 키워드 기반 관련 데이터 찾기
        keywords = user_input.lower().split()
        
        # 패션 관련 키워드 확장
        fashion_keywords = []
        for keyword in keywords:
            fashion_keywords.append(keyword)
            # 키워드 확장 (예: "셔츠" -> "셔츠", "티셔츠", "가디건" 등)
            if keyword in ["셔츠", "티", "상의"]:
                fashion_keywords.extend(["셔츠", "티셔츠", "가디건", "니트", "맨투맨"])
            elif keyword in ["바지", "팬츠", "하의"]:
                fashion_keywords.extend(["바지", "팬츠", "슬랙스", "청바지", "치노"])
            elif keyword in ["데이트", "소개팅"]:
                fashion_keywords.extend(["데이트", "소개팅", "카페", "데이트룩"])
            elif keyword in ["출근", "면접", "직장"]:
                fashion_keywords.extend(["출근", "면접", "직장", "비즈니스"])
        
        # 패션 아이템 관련
        for item in self.fashion_reference_data['fashion_items']:
            item_lower = item['item'].lower()
            if any(keyword in item_lower for keyword in fashion_keywords):
                relevant_data.append(f"📦 {item['item']}: {item['description']} - {item['styling_tips']}")
        
        # 아웃핏 조합 관련
        for combo in self.fashion_reference_data['outfit_combinations']:
            combo_lower = combo['combination'].lower()
            items_lower = [item.lower() for item in combo['items']]
            occasion_lower = combo['occasion'].lower()
            
            if (any(keyword in combo_lower for keyword in fashion_keywords) or
                any(keyword in occasion_lower for keyword in fashion_keywords) or
                any(any(keyword in item for keyword in fashion_keywords) for item in items_lower)):
                relevant_data.append(f"👔 {combo['combination']}: {', '.join(combo['items'])} - {combo['occasion']}")
        
        # 컬러 추천 관련
        for color in self.fashion_reference_data['color_recommendations']:
            color_lower = color['color'].lower()
            if any(keyword in color_lower for keyword in fashion_keywords):
                relevant_data.append(f"🎨 {color['color']}: {color['description']}")
        
        # 스타일링 팁 관련 (일반적인 팁들)
        if len(relevant_data) < 3:  # 관련 데이터가 적으면 일반 팁들도 추가
            for tip in self.fashion_reference_data['styling_tips'][:3]:
                relevant_data.append(f"💡 {tip}")
        
        # 계절별 조언 추가 (관련성이 있을 때)
        if any(keyword in ["여름", "겨울", "봄", "가을", "계절"] for keyword in keywords):
            for advice in self.fashion_reference_data['seasonal_advice'][:2]:
                relevant_data.append(f"🌤️ 계절 조언: {advice}")
        
        return "\n".join(relevant_data) if relevant_data else ""
    
    async def _generate_response_from_reference_data(self, user_input: str, expert_type: FashionExpertType) -> str:
        """참고 데이터를 기반으로 직접 응답 생성 (JSON 데이터만 사용)"""
        print(f"🔍 참고 데이터 기반 응답 생성 시작: {user_input}")
        
        try:
            # JSON 데이터에서 실제 추천 추출 (강제로 JSON 데이터만 사용)
            actual_items = []
            actual_combos = []
            actual_colors = []
            
            # 1. 사용자 입력과 직접 매칭되는 데이터 찾기
            user_keywords = user_input.lower().split()
            
            # 키워드 확장 (더 정확한 매칭을 위해)
            expanded_keywords = user_keywords.copy()
            for keyword in user_keywords:
                # 부분 매칭을 위한 키워드 확장
                if '소개팅' in keyword:
                    expanded_keywords.extend(['소개팅', '데이트', '미팅'])
                elif '데이트' in keyword:
                    expanded_keywords.extend(['데이트', '소개팅', '카페'])
                elif '출근' in keyword:
                    expanded_keywords.extend(['출근', '직장', '비즈니스', '미팅'])
            
            print(f"🔍 원본 키워드: {user_keywords}")
            print(f"🔍 확장된 키워드: {expanded_keywords}")
            
            # 확장된 키워드 사용
            user_keywords = expanded_keywords
            
            # 패션 아이템 매칭
            for item in self.fashion_reference_data['fashion_items']:
                if any(keyword in item['item'].lower() for keyword in user_keywords):
                    actual_items.append(item)
            
            # 아웃핏 조합 매칭
            for combo in self.fashion_reference_data['outfit_combinations']:
                # items가 리스트인지 확인하고 안전하게 처리
                items_list = combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]
                
                # occasion이 문자열인지 확인하고 안전하게 처리
                occasion_str = ""
                if combo['occasion'] is not None:
                    if isinstance(combo['occasion'], str):
                        occasion_str = combo['occasion'].lower()
                    else:
                        occasion_str = str(combo['occasion']).lower()
                
                # 각 조건을 개별적으로 확인
                # combination_match = any(keyword in combo['combination'].lower() for keyword in user_keywords)  # 조합명 매칭 제거
                items_match = any(any(keyword in item.lower() for keyword in user_keywords) for item in items_list)
                occasion_match = any(keyword in occasion_str for keyword in user_keywords) if occasion_str else False
                
                # 디버깅: 매칭 과정 출력
                if user_keywords and any(keyword in ['소개팅', '데이트', '출근'] for keyword in user_keywords):
                    print(f"🔍 매칭 확인: '{combo['combination']}' (occasion: '{combo['occasion']}')")
                    print(f"   user_keywords: {user_keywords}")
                    print(f"   occasion_str: '{occasion_str}'")
                    print(f"   occasion_match: {occasion_match}")
                    if occasion_match:
                        print(f"   ✅ 매칭 성공!")
                
                # 디버깅 출력
                if occasion_match:
                    print(f"🎯 매칭 발견: '{combo['combination']}' (occasion: '{combo['occasion']}')")
                
                if items_match or occasion_match:  # combination_match 제거
                    actual_combos.append(combo)
            
            # 컬러 추천 매칭
            for color in self.fashion_reference_data['color_recommendations']:
                if any(keyword in color['color'].lower() for keyword in user_keywords):
                    actual_colors.append(color)
            
            print(f"🎯 직접 매칭: 아이템={len(actual_items)}, 조합={len(actual_combos)}, 컬러={len(actual_colors)}")
            
            # 2. 직접 매칭이 없으면 가장 유사한 데이터 찾기
            if not actual_items and not actual_combos and not actual_colors:
                # print("⚠️ 직접 매칭 없음 - 유사한 데이터 찾기")
                
                # 상황별 유사 데이터 찾기
                if any(keyword in ["데이트", "소개팅", "카페"] for keyword in user_keywords):
                    # 데이트 관련 데이터 찾기
                    for combo in self.fashion_reference_data['outfit_combinations']:
                        occasion_str = ""
                        if combo['occasion'] is not None:
                            if isinstance(combo['occasion'], str):
                                occasion_str = combo['occasion'].lower()
                            else:
                                occasion_str = str(combo['occasion']).lower()
                        
                        if any(word in occasion_str for word in ["데이트", "카페", "소개팅"]):
                            actual_combos.append(combo)
                            break
                
                elif any(keyword in ["출근", "면접", "직장", "비즈니스"] for keyword in user_keywords):
                    # 출근 관련 데이터 찾기
                    for combo in self.fashion_reference_data['outfit_combinations']:
                        occasion_str = ""
                        if combo['occasion'] is not None:
                            if isinstance(combo['occasion'], str):
                                occasion_str = combo['occasion'].lower()
                            else:
                                occasion_str = str(combo['occasion']).lower()
                        
                        if any(word in occasion_str for word in ["출근", "직장", "비즈니스"]):
                            actual_combos.append(combo)
                            break
                
                elif any(keyword in ["여름", "겨울", "봄", "가을"] for keyword in user_keywords):
                    # 계절 관련 데이터 찾기
                    for combo in self.fashion_reference_data['outfit_combinations']:
                        occasion_str = ""
                        if combo['occasion'] is not None:
                            if isinstance(combo['occasion'], str):
                                occasion_str = combo['occasion'].lower()
                            else:
                                occasion_str = str(combo['occasion']).lower()
                        
                        if any(word in occasion_str for word in ["여름", "데일리", "캐주얼"]):
                            actual_combos.append(combo)
                            break
                
                # 여전히 없으면 첫 번째 데이터 사용
                if not actual_items and not actual_combos and not actual_colors:
                    if self.fashion_reference_data['outfit_combinations']:
                        actual_combos.append(self.fashion_reference_data['outfit_combinations'][0])
                    if self.fashion_reference_data['color_recommendations']:
                        actual_colors.append(self.fashion_reference_data['color_recommendations'][0])
                    if self.fashion_reference_data['fashion_items']:
                        actual_items.append(self.fashion_reference_data['fashion_items'][0])
            
            # 전문가별 응답 생성 (JSON 데이터 기반 자연스러운 답변)
            expert_responses = {
                FashionExpertType.STYLE_ANALYST: {
                    "prefix": "체형을 보니",
                    "focus": "핏감과 실루엣",
                    "style": "핏감 중심의 깔끔한 스타일"
                },
                FashionExpertType.TREND_EXPERT: {
                    "prefix": "요즘 핫한 건",
                    "focus": "트렌드",
                    "style": "트렌디하고 세련된 스타일"
                },
                FashionExpertType.COLOR_EXPERT: {
                    "prefix": "색상으로는",
                    "focus": "컬러 조합",
                    "style": "색상 조합이 완벽한 스타일"
                },
                FashionExpertType.FITTING_COORDINATOR: {
                    "prefix": "전체적으로는",
                    "focus": "종합적인 스타일링",
                    "style": "균형잡힌 완벽한 스타일"
                }
            }
            
            template = expert_responses.get(expert_type, expert_responses[FashionExpertType.STYLE_ANALYST])
            
            # JSON 데이터 기반 응답 생성 (강제로 JSON 데이터만 사용)
            response_parts = []
            
            # 1. 실제 아웃핏 조합이 있으면 그것을 우선 추천
            if actual_combos:
                # 전문가별로 다른 선택 로직 적용
                combo = None
                # print(f"🔍 {len(actual_combos)}개 조합 중에서 {expert_type.value} 전문가 기준으로 선택 중...")
                
                # 전문가별 필터링 및 우선순위
                if expert_type == FashionExpertType.STYLE_ANALYST:
                    # 스타일 분석가: 핏감 중심, 깔끔한 스타일 선호
                    for c in actual_combos:
                        items = c['items'] if isinstance(c['items'], list) else [str(c['items'])]
                        # 슬림핏, 레귤러핏 관련 아이템 우선
                        if any(keyword in str(item).lower() for item in items for keyword in ['슬림', '레귤러', '셔츠', '슬랙스']):
                            combo = c
                            # print(f"✅ 스타일 분석가 선택: '{c['combination']}' (핏감 중심)")
                            break
                
                elif expert_type == FashionExpertType.TREND_EXPERT:
                    # 트렌드 전문가: 트렌디한 스타일 선호
                    for c in actual_combos:
                        items = c['items'] if isinstance(c['items'], list) else [str(c['items'])]
                        # 오버핏, 와이드핏, 트렌디한 아이템 우선
                        if any(keyword in str(item).lower() for item in items for keyword in ['오버', '와이드', '니트', '맨투맨', '후드']):
                            combo = c
                            # print(f"✅ 트렌드 전문가 선택: '{c['combination']}' (트렌디)")
                            break
                
                elif expert_type == FashionExpertType.COLOR_EXPERT:
                    # 컬러 전문가: 색상 조합 중심
                    for c in actual_combos:
                        items = c['items'] if isinstance(c['items'], list) else [str(c['items'])]
                        # 모노톤, 톤온톤 관련 아이템 우선
                        if any(keyword in str(item).lower() for item in items for keyword in ['블랙', '화이트', '그레이', '베이지', '모노']):
                            combo = c
                            # print(f"✅ 컬러 전문가 선택: '{c['combination']}' (색상 조합)")
                            break
                
                elif expert_type == FashionExpertType.FITTING_COORDINATOR:
                    # 피팅 코디네이터: 균형잡힌 스타일 선호
                    for c in actual_combos:
                        items = c['items'] if isinstance(c['items'], list) else [str(c['items'])]
                        # 자켓, 가디건 등 레이어드 스타일 우선
                        if any(keyword in str(item).lower() for item in items for keyword in ['자켓', '가디건', '카디건', '블레이저']):
                            combo = c
                            # print(f"✅ 피팅 코디네이터 선택: '{c['combination']}' (균형잡힌)")
                            break
                
                # 소개팅/데이트 특화 우선순위 (모든 전문가 공통)
                if any(keyword in ['소개팅', '데이트'] for keyword in user_keywords):
                    # 스트라이프 셔츠 제외 로직
                    if combo and isinstance(combo['items'], list):
                        items = combo['items']
                        if any('스트라이프' in str(item) for item in items):
                            # 스트라이프 셔츠가 포함된 경우 다른 조합 찾기
                            for c in actual_combos:
                                if c != combo:
                                    items = c['items'] if isinstance(c['items'], list) else [str(c['items'])]
                                    if not any('스트라이프' in str(item) for item in items):
                                        combo = c
                                        # print(f"✅ 스트라이프 셔츠 제외, 대체 조합 선택: '{c['combination']}'")
                                        break
                
                # 전문가별 선택이 실패한 경우 일반적인 우선순위
                if combo is None:
                    # 1순위: occasion이 정확히 매칭되는 것
                    for c in actual_combos:
                        if c.get('occasion') and any(keyword in c['occasion'].lower() for keyword in user_keywords):
                            combo = c
                            # print(f"✅ occasion 매칭으로 선택: '{c['combination']}' (occasion: '{c['occasion']}')")
                            break
                    
                    # 2순위: 첫 번째 조합 사용
                    if combo is None and actual_combos:
                        combo = actual_combos[0]
                        # print(f"⚠️ 전문가별 선택 실패, 첫 번째 조합 사용: '{combo['combination']}'")
                
                # JSON 데이터 기반 자연스러운 답변 생성
                if expert_type == FashionExpertType.STYLE_ANALYST:
                    response_parts.append(f"체형을 보니 {combo['combination']}이 핏감과 실루엣에 잘 어울려.")
                elif expert_type == FashionExpertType.TREND_EXPERT:
                    response_parts.append(f"요즘 트렌드를 보면 {combo['combination']}이 인기 있어.")
                elif expert_type == FashionExpertType.COLOR_EXPERT:
                    response_parts.append(f"색상 조합으로 보면 {combo['combination']}이 퍼스널 컬러랑 잘 어울릴 것 같아.")
                elif expert_type == FashionExpertType.FITTING_COORDINATOR:
                    response_parts.append(f"전체적으로 {combo['combination']}이 균형감이 좋은 조합이에.")
                else:
                    response_parts.append(f"{template['prefix']} {combo['combination']}이 {template['focus']}에 잘 어울릴 것 같아.")
                
                # items가 리스트인지 확인하고 안전하게 처리
                if isinstance(combo['items'], list):
                    # 각 아이템별 상세 정보 추가
                    detailed_items = []
                    for item_name in combo['items']:
                        # JSON 데이터에서 상세 정보 찾기
                        item_details = self._get_item_details(item_name)
                        if item_details:
                            detailed_item = self._format_item_with_details(item_name, item_details)
                            detailed_items.append(detailed_item)
                        else:
                            # JSON에서 못 찾으면 기본 형태로
                            detailed_items.append(item_name)
                    items_str = ', '.join(detailed_items)
                else:
                    items_str = str(combo['items'])
                
                response_parts.append(f"구체적으로는 {items_str} 조합을 추천해.")
                
                # 추가 정보 제공 (JSON 데이터 활용)
                if combo.get('occasion'):
                    response_parts.append(f"이 조합은 {combo['occasion']}에 특히 어울려.")
                
                # 각 아이템별 논리적 근거 설명
                if isinstance(combo['items'], list) and combo['items']:
                    response_parts.append("")
                    # 여름 컬러 팁 추가
                    response_parts.append(f"🎨 베이지나 화이트 톤으로 통일하면 여름다워!")
                
                print(f"✅ 아웃핏 조합 기반 응답 생성: {combo['combination']}")
                print(f"📋 사용된 JSON 데이터: {combo}")
            
            # 2. 실제 컬러 추천이 있으면 추가 (아웃핏 조합이 없을 때만)
            elif actual_colors:
                color = actual_colors[0]
                response_parts.append(f"{template['prefix']} {color['color']} 컬러가 {template['focus']}에 좋아!")
                response_parts.append(f"{color['description']}")
                
                print(f"✅ 컬러 추천 기반 응답 생성: {color['color']}")
                print(f"📋 사용된 JSON 데이터: {color}")
            
            # 3. 실제 패션 아이템이 있으면 추가 (아웃핏 조합과 컬러가 없을 때만)
            elif actual_items:
                item = actual_items[0]
                response_parts.append(f"{template['prefix']} {item['item']}이 {template['focus']}에 완벽해!")
                response_parts.append(f"{item['description']}")
                
                print(f"✅ 패션 아이템 기반 응답 생성: {item['item']}")
                print(f"📋 사용된 JSON 데이터: {item}")
            
            # 4. 간단한 스타일링 팁 추가 (아웃핏 조합이 없을 때만)
            if self.fashion_reference_data['styling_tips'] and not actual_combos:
                tip = self.fashion_reference_data['styling_tips'][0]
                # 팁이 너무 길면 첫 번째 문장만 사용
                if len(tip) > 50:
                    tip = tip.split('.')[0] + '.'
                response_parts.append(f"💡 {tip}")
            
            # 5. 절대적으로 JSON 데이터가 없으면 강제로 첫 번째 데이터 사용
            if not response_parts:
                # print("⚠️ 매칭된 데이터 없음 - 강제로 첫 번째 데이터 사용")
                
                if self.fashion_reference_data['outfit_combinations']:
                    combo = self.fashion_reference_data['outfit_combinations'][0]
                    response_parts.append(f"{template['prefix']} {combo['combination']}이 {template['focus']}에 완벽해!")
                    
                    if isinstance(combo['items'], list):
                        items_str = ', '.join(combo['items'])
                    else:
                        items_str = str(combo['items'])
                    
                    response_parts.append(f"{items_str} 조합을 추천해!")
                    
                    if combo.get('occasion'):
                        response_parts.append(f"이 조합은 {combo['occasion']}에 특히 어울려!")
                
                elif self.fashion_reference_data['fashion_items']:
                    item = self.fashion_reference_data['fashion_items'][0]
                    response_parts.append(f"{template['prefix']} {item['item']}이 {template['focus']}에 완벽해!")
                    response_parts.append(f"{item['description']}")
                
                elif self.fashion_reference_data['color_recommendations']:
                    color = self.fashion_reference_data['color_recommendations'][0]
                    response_parts.append(f"{template['prefix']} {color['color']} 컬러가 {template['focus']}에 좋아!")
                    response_parts.append(f"{color['description']}")
                
                # print(f"✅ 강제 데이터 사용 완료")
            
            final_response = " ".join(response_parts)
            # print(f"🎉 최종 응답 (JSON 데이터 기반): {final_response}")
            return final_response
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            # 오류 발생 시 기본 메시지 반환
            return f"체형을 보니 기본 스타일이 핏감과 실루엣에 좋아! JSON 데이터를 기반으로 한 추천을 제공해!"
    
    async def _generate_default_json_response(self, user_input: str, expert_type: FashionExpertType) -> str:
        """기본 JSON 데이터를 사용한 응답 생성 (간단하게)"""
        # print(f"🔧 기본 JSON 데이터 응답 생성: {user_input}")
        
        # JSON 데이터가 있는지 확인 (없어도 강제로 기본 메시지 생성)
        if not self.fashion_reference_data['outfit_combinations'] and \
           not self.fashion_reference_data['color_recommendations'] and \
           not self.fashion_reference_data['fashion_items']:
            # print("⚠️ JSON 데이터가 없음 - 기본 메시지 생성")
            return f"스타일로는 기본 조합이 좋아! JSON 데이터를 기반으로 한 추천을 제공해!"
        
        # 전문가별 응답 템플릿 (정직한 표현으로 수정)
        expert_responses = {
            FashionExpertType.STYLE_ANALYST: {
                "prefix": "스타일로는",
                "focus": "핏감과 실루엣"
            },
            FashionExpertType.TREND_EXPERT: {
                "prefix": "요즘 트렌드로는",
                "focus": "트렌드"
            },
            FashionExpertType.COLOR_EXPERT: {
                "prefix": "색상으로는",
                "focus": "컬러 조합"
            },
            FashionExpertType.FITTING_COORDINATOR: {
                "prefix": "전체적으로는",
                "focus": "종합적인 스타일링"
            }
        }
        
        template = expert_responses.get(expert_type, expert_responses[FashionExpertType.STYLE_ANALYST])
        
        # JSON 데이터에서 첫 번째 데이터 사용
        response_parts = []
        
        if self.fashion_reference_data['outfit_combinations']:
            combo = self.fashion_reference_data['outfit_combinations'][0]
            response_parts.append(f"{template['prefix']} {combo['combination']}이 {template['focus']}에 완벽해!")
            
            # items가 리스트인지 확인하고 안전하게 처리
            if isinstance(combo['items'], list):
                # 각 아이템별 상세 정보 추가 (색상만)
                detailed_items = []
                for item_name in combo['items']:
                    item_details = self._get_item_details(item_name)
                    if item_details:
                        detailed_item = self._format_item_with_details(item_name, item_details)
                        detailed_items.append(detailed_item)
                    else:
                        detailed_items.append(item_name)
                items_str = ', '.join(detailed_items)
            else:
                items_str = str(combo['items'])
            
            response_parts.append(f"구체적으로는 {items_str} 조합을 추천해!")
            # print(f"✅ 기본 아웃핏 조합 사용: {combo['combination']}")
        
        elif self.fashion_reference_data['color_recommendations']:
            color = self.fashion_reference_data['color_recommendations'][0]
            response_parts.append(f"{template['prefix']} {color['color']} 컬러가 {template['focus']}에 좋아!")
            response_parts.append(f"{color['description']}")
            # print(f"✅ 기본 컬러 추천 사용: {color['color']}")
        
        elif self.fashion_reference_data['fashion_items']:
            item = self.fashion_reference_data['fashion_items'][0]
            response_parts.append(f"{template['prefix']} {item['item']}이 {template['focus']}에 완벽해!")
            response_parts.append(f"{item['description']}")
            # print(f"✅ 기본 패션 아이템 사용: {item['item']}")
        
        # 여름 스타일링 팁 추가
        if self.fashion_reference_data['styling_tips']:
            tip = self.fashion_reference_data['styling_tips'][0]
            # 팁이 너무 길면 첫 번째 문장만 사용
            if len(tip) > 50:
                tip = tip.split('.')[0] + '.'
            response_parts.append(f"💡 {tip}")
        
        final_response = " ".join(response_parts)
        # print(f"🎉 기본 JSON 응답: {final_response}")
        return final_response
    
    async def _generate_forced_json_response(self, expert_type: FashionExpertType) -> str:
        """강제로 JSON 데이터를 사용한 응답 생성 (간단하게)"""
        # print(f"🚨 강제 JSON 데이터 응답 생성")
        
        # 전문가별 응답 템플릿 (정직한 표현으로 수정)
        expert_responses = {
            FashionExpertType.STYLE_ANALYST: {
                "prefix": "스타일로는",
                "focus": "핏감과 실루엣"
            },
            FashionExpertType.TREND_EXPERT: {
                "prefix": "요즘 트렌드로는",
                "focus": "트렌드"
            },
            FashionExpertType.COLOR_EXPERT: {
                "prefix": "색상으로는",
                "focus": "컬러 조합"
            },
            FashionExpertType.FITTING_COORDINATOR: {
                "prefix": "전체적으로는",
                "focus": "종합적인 스타일링"
            }
        }
        
        template = expert_responses.get(expert_type, expert_responses[FashionExpertType.STYLE_ANALYST])
        
        # JSON 데이터에서 무조건 첫 번째 데이터 사용
        response_parts = []
        
        # 아웃핏 조합이 있으면 사용
        if self.fashion_reference_data['outfit_combinations']:
            combo = self.fashion_reference_data['outfit_combinations'][0]
            response_parts.append(f"{template['prefix']} {combo['combination']}이 {template['focus']}에 완벽해!")
            
            # items가 리스트인지 확인하고 안전하게 처리
            if isinstance(combo['items'], list):
                # 각 아이템별 상세 정보 추가 (색상만)
                detailed_items = []
                for item_name in combo['items']:
                    item_details = self._get_item_details(item_name)
                    if item_details:
                        detailed_item = self._format_item_with_details(item_name, item_details)
                        detailed_items.append(detailed_item)
                    else:
                        detailed_items.append(item_name)
                items_str = ', '.join(detailed_items)
            else:
                items_str = str(combo['items'])
            
            response_parts.append(f"구체적으로는 {items_str} 조합을 추천해!")
            
            # 여름 컬러 팁 추가
            response_parts.append(f"🎨 베이지나 화이트 톤으로 통일하면 여름다워!")
            
            # print(f"🚨 강제 아웃핏 조합 사용: {combo['combination']}")
            # print(f"📋 사용된 JSON 데이터: {combo}")
        
        # 컬러 추천이 있으면 추가
        elif self.fashion_reference_data['color_recommendations']:
            color = self.fashion_reference_data['color_recommendations'][0]
            response_parts.append(f"{template['prefix']} {color['color']} 컬러가 {template['focus']}에 좋아!")
            response_parts.append(f"{color['description']}")
            # print(f"🚨 강제 컬러 추천 사용: {color['color']}")
            # print(f"📋 사용된 JSON 데이터: {color}")
        
        # 패션 아이템이 있으면 사용
        elif self.fashion_reference_data['fashion_items']:
            item = self.fashion_reference_data['fashion_items'][0]
            response_parts.append(f"{template['prefix']} {item['item']}이 {template['focus']}에 완벽해!")
            response_parts.append(f"{item['description']}")
            # print(f"🚨 강제 패션 아이템 사용: {item['item']}")
            # print(f"📋 사용된 JSON 데이터: {item}")
        
        # 여름 스타일링 팁 추가
        if self.fashion_reference_data['styling_tips']:
            tip = self.fashion_reference_data['styling_tips'][0]
            # 팁이 너무 길면 첫 번째 문장만 사용
            if len(tip) > 50:
                tip = tip.split('.')[0] + '.'
            response_parts.append(f"💡 {tip}")
        
        # 절대적으로 아무것도 없으면 기본 메시지
        if not response_parts:
            response_parts.append(f"스타일로는 기본 조합이 좋아!")
            response_parts.append("JSON 데이터를 기반으로 한 추천을 제공해!")
        
        final_response = " ".join(response_parts)
        # print(f"🎉 강제 JSON 응답: {final_response}")
        return final_response

    async def _generate_json_based_response(self, user_input: str, expert_type: FashionExpertType, json_data: dict = None) -> str:
        """JSON 데이터를 기반으로 자연스럽고 다양한 대화 스타일로 답변 생성"""
        
        # JSON 데이터가 없으면 기본 데이터 사용
        if not json_data:
            json_data = {
                "top": {"item": "긴팔 셔츠", "color": "화이트", "fit": "레귤러핏", "material": "면"},
                "bottom": {"item": "와이드 슬랙스", "color": "베이지", "fit": "와이드핏", "material": "린넨"},
                "shoes": {"item": "로퍼", "color": "브라운", "style": "캐주얼"},
                "styling_methods": {
                    "top_wearing_method": "앞부분만 살짝 넣기",
                    "tuck_degree": "앞부분만 넣기",
                    "fit_details": "어깨 딱 맞게, 가슴 여유있게",
                    "silhouette_balance": "상하의 길이 비율이 균형잡힘",
                    "styling_points": "소매 롤업, 버튼 위쪽 1-2개 해제"
                }
            }
        
        # JSON 데이터에서 정보 추출
        top_info = json_data.get("top", {})
        bottom_info = json_data.get("bottom", {})
        shoes_info = json_data.get("shoes", {})
        styling_info = json_data.get("styling_methods", {})
        
        # 전문가별 다양한 대화 스타일
        import random
        
        expert_responses = {
            FashionExpertType.STYLE_ANALYST: [
                f"{top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 나쁘지 않아. {styling_info.get('styling_points', '')} 포인트가 괜찮아.",
                f"체형에 {top_info.get('item', '')}이 적당해. {styling_info.get('fit_details', '')}라서 날씬해 보일 거야. {bottom_info.get('color', '')} {bottom_info.get('item', '')}도 잘 어울려.",
                f"{top_info.get('color', '')} {top_info.get('item', '')}이 괜찮네. {styling_info.get('fit_details', '')}라서 체형이 좀 보완될 거야. {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 나쁘지 않아.",
                f"{styling_info.get('tuck_degree', '')} 스타일링이 좀 아쉽다. {styling_info.get('silhouette_balance', '')}를 위해 다른 방법은 어떨까?",
                f"핏감은 괜찮아. {top_info.get('fit', '')}라서 체형을 보완해줘. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 좋아."
            ],
            FashionExpertType.TREND_EXPERT: [
                f"{top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 요즘 유행이야. {styling_info.get('silhouette_balance', '')}가 괜찮아.",
                f"이 조합 인스타에서 자주 보여. {styling_info.get('fit_details', '')}가 트렌디해. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')}이 핫해.",
                f"{top_info.get('item', '')} 요즘 많이 입어. {top_info.get('color', '')} 컬러가 이번 시즌에 괜찮아. {bottom_info.get('color', '')} {bottom_info.get('item', '')}도 트렌디해.",
                f"{styling_info.get('styling_points', '')} 스타일링이 좀 올드해. 요즘은 다른 방법이 더 인기 있어.",
                f"요즘 트렌드를 보면 {top_info.get('material', '')} {top_info.get('item', '')}이 괜찮아. {top_info.get('material', '')} 소재도 핫해. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 인기야."
            ],
            FashionExpertType.COLOR_EXPERT: [
                f"{top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 괜찮아. 톤온톤이 나쁘지 않아.",
                f"퍼스널 컬러랑 어울려. {top_info.get('color', '')}가 피부톤을 밝게 해줘. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 좋아.",
                f"색상 밸런스가 괜찮아. {styling_info.get('styling_points', '')} 포인트도 색상과 잘 맞아.",
                f"색상 조합이 좀 어색해. {top_info.get('color', '')} 대신 다른 색상은 어떨까?",
                f"톤온톤 조합이 나쁘지 않아. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')}이 잘 어우러져."
            ],
            FashionExpertType.FITTING_COORDINATOR: [
                f"{top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 괜찮아. {styling_info.get('silhouette_balance', '')}가 나쁘지 않아.",
                f"이 룩 괜찮아. {styling_info.get('fit_details', '')}와 {styling_info.get('tuck_degree', '')}가 균형잡혀 있어. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 좋아.",
                f"피팅 관점에서는 괜찮아. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합도 나쁘지 않아.",
                f"전체적으로는 좋은데 {styling_info.get('styling_points', '')} 부분을 조금 바꾸면 더 나을 것 같아.",
                f"전체적으로 균형감이 괜찮아. {top_info.get('color', '')} {top_info.get('item', '')} + {bottom_info.get('color', '')} {bottom_info.get('item', '')} 조합이 잘 맞아."
            ]
        }
        
        # 해당 전문가의 응답 풀에서 랜덤 선택
        response_pool = expert_responses.get(expert_type, expert_responses[FashionExpertType.STYLE_ANALYST])
        response = random.choice(response_pool)
        
        # 추가 정보 (신발, 액세서리 등) - 신발은 항상 추천 (기호 사용)
        if shoes_info.get("item"):
            # 색상 중복 방지
            shoe_color = shoes_info.get('color', '')
            shoe_item = shoes_info.get('item', '')
            if shoe_color and shoe_item:
                # 색상이 이미 아이템명에 포함되어 있으면 색상 생략
                if shoe_color.lower() in shoe_item.lower():
                    response += f" + {shoe_item}"
                else:
                    response += f" + {shoe_color} {shoe_item}"
            else:
                response += f" + {shoe_item}"
        
        return response

    async def get_single_expert_analysis(self, request: ExpertAnalysisRequest):
        """단일 전문가 분석"""
        expert_profile = self.expert_profiles[request.expert_type]
        
        # print(f"\n🚀 전문가 분석 시작: {request.expert_type.value}")
        # print(f"📝 사용자 입력: {request.user_input}")
        
        # JSON 데이터 기반 응답 시도 (새로운 방식)
        if hasattr(request, 'json_data') and request.json_data:
            json_based_response = await self._generate_json_based_response(
                request.user_input, 
                request.expert_type,
                request.json_data
            )
            return {
                "expert_type": request.expert_type.value,
                "expert_role": expert_profile["role"],
                "analysis": json_based_response,
                "expertise_areas": expert_profile["expertise"],
                "response_source": "json_data"
            }
        
        # 1단계: 참고 데이터 기반 직접 응답 시도
        # print("🔍 1단계: 참고 데이터 기반 응답 시도")
        reference_based_response = await self._generate_response_from_reference_data(
            request.user_input, 
            request.expert_type
        )
        
        # print(f"✅ 참고 데이터 기반 응답 성공!")
        # logger.info(f"참고 데이터 기반 응답 사용 - {request.expert_type}")
        return {
            "expert_type": request.expert_type.value,
            "expert_role": expert_profile["role"],
            "analysis": reference_based_response,
            "expertise_areas": expert_profile["expertise"],
            "response_source": "reference_data"
        }
    
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
    
    def _get_item_details(self, item_name: str) -> Dict:
        """아이템의 상세 정보 (색상만) 가져오기"""
        # JSON 데이터에서 해당 아이템 찾기
        for item in self.fashion_reference_data['fashion_items']:
            if item.get('item') == item_name:
                return {
                    'color': item.get('color', ''),
                    'description': item.get('description', '')
                }
        return {}
    

    
    def _format_item_with_details(self, item_name: str, item_details: Dict) -> str:
        """아이템명과 색상만 포맷팅"""
        if not item_details or not item_details.get('color'):
            return item_name
        
        return f"{item_name} ({item_details['color']})"
    
    async def analyze_image_with_fashion_data(self, image_analysis: str | Dict) -> Dict:
        """이미지 분석 결과를 패션 데이터와 매칭"""
        try:
            print(f"🔍 이미지 분석 결과와 패션 데이터 매칭 시작")
            
            # 이미지 분석 결과가 이미 Dict인 경우 (새로운 JSON 형식)
            if isinstance(image_analysis, dict):
                extracted_items = image_analysis
                print("✅ JSON 형식 분석 결과 사용")
            else:
                # 기존 텍스트 형식인 경우 파싱
                extracted_items = self._extract_items_from_analysis(image_analysis)
                print("✅ 텍스트 형식 분석 결과 파싱 완료")
            
            # 패션 데이터와 매칭
            matched_data = self._match_with_fashion_data(extracted_items)
            
            # 매칭 결과 종합
            result = {
                "extracted_items": extracted_items,
                "matched_fashion_data": matched_data,
                "recommendations": self._generate_recommendations_from_matching(matched_data, extracted_items)
            }
            
            print(f"✅ 패션 데이터 매칭 완료")
            return result
            
        except Exception as e:
            print(f"❌ 패션 데이터 매칭 실패: {e}")
            return {
                "error": f"매칭 실패: {str(e)}",
                "extracted_items": extracted_items if 'extracted_items' in locals() else None
            }
    
    def _extract_items_from_analysis(self, analysis: str) -> Dict:
        """이미지 분석 텍스트에서 아이템 정보와 스타일링 방법 추출"""
        items = {
            "top": {"item": "", "color": "", "fit": "", "material": "", "length": ""},
            "bottom": {"item": "", "color": "", "fit": "", "material": "", "length": ""},
            "shoes": {"item": "", "color": "", "style": ""},
            "accessories": [],
            "styling_methods": {
                "top_wearing_method": "",  # 상의 착용법
                "tuck_degree": "",         # 상의 넣는 정도
                "fit_details": "",         # 핏감 상세
                "silhouette_balance": "",  # 실루엣 밸런스
                "styling_points": ""       # 스타일링 포인트
            }
        }
        
        lines = analysis.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 섹션 구분
            if "상의 분석" in line:
                current_section = "top"
            elif "하의 분석" in line:
                current_section = "bottom"
            elif "신발 분석" in line:
                current_section = "shoes"
            elif "액세서리 분석" in line:
                current_section = "accessories"
            elif "스타일링 방법 분석" in line:
                current_section = "styling"
            
            # 아이템 정보 추출
            if current_section and ":" in line:
                if "아이템명:" in line:
                    item_name = line.split(":")[1].strip().replace("(", "").replace(")", "")
                    if current_section in ["top", "bottom", "shoes"]:
                        items[current_section]["item"] = item_name
                elif "색상:" in line:
                    color = line.split(":")[1].strip()
                    if current_section in ["top", "bottom", "shoes"]:
                        items[current_section]["color"] = color
                elif "핏:" in line:
                    fit = line.split(":")[1].strip()
                    if current_section in ["top", "bottom"]:
                        items[current_section]["fit"] = fit
                elif "소재:" in line:
                    material = line.split(":")[1].strip()
                    if current_section in ["top", "bottom"]:
                        items[current_section]["material"] = material
                elif "길이:" in line:
                    length = line.split(":")[1].strip()
                    if current_section in ["top", "bottom"]:
                        items[current_section]["length"] = length
                elif "스타일:" in line:
                    style = line.split(":")[1].strip()
                    if current_section == "shoes":
                        items[current_section]["style"] = style
                
                # 스타일링 방법 정보 추출
                elif current_section == "styling":
                    if "상의 착용법:" in line:
                        items["styling_methods"]["top_wearing_method"] = line.split(":")[1].strip()
                    elif "상의 넣는 정도:" in line:
                        items["styling_methods"]["tuck_degree"] = line.split(":")[1].strip()
                    elif "핏감:" in line:
                        items["styling_methods"]["fit_details"] = line.split(":")[1].strip()
                    elif "실루엣 밸런스:" in line:
                        items["styling_methods"]["silhouette_balance"] = line.split(":")[1].strip()
                    elif "스타일링 포인트:" in line:
                        items["styling_methods"]["styling_points"] = line.split(":")[1].strip()
        
        return items
    
    def _match_with_fashion_data(self, extracted_items: Dict) -> Dict:
        """추출된 아이템을 패션 데이터와 매칭"""
        matches = {
            "exact_matches": [],
            "similar_matches": [],
            "color_matches": [],
            "style_matches": []
        }
        
        # 상의 매칭
        if extracted_items["top"]["item"]:
            top_matches = self._find_item_matches(extracted_items["top"], "fashion_items")
            matches["exact_matches"].extend(top_matches)
        
        # 하의 매칭
        if extracted_items["bottom"]["item"]:
            bottom_matches = self._find_item_matches(extracted_items["bottom"], "fashion_items")
            matches["exact_matches"].extend(bottom_matches)
        
        # 전체 아웃핏 조합 매칭
        outfit_matches = self._find_outfit_matches(extracted_items)
        matches["similar_matches"].extend(outfit_matches)
        
        # 컬러 매칭
        color_matches = self._find_color_matches(extracted_items)
        matches["color_matches"].extend(color_matches)
        
        return matches
    
    def _find_item_matches(self, item: Dict, data_type: str) -> List[Dict]:
        """개별 아이템 매칭"""
        matches = []
        
        for data_item in self.fashion_reference_data[data_type]:
            score = 0
            
            # 아이템명 매칭
            if item["item"] and item["item"] in data_item.get("item", ""):
                score += 3
            
            # 색상 매칭
            if item["color"] and item["color"] in data_item.get("color", ""):
                score += 2
            
            # 소재 매칭
            if item["material"] and item["material"] in data_item.get("description", ""):
                score += 1
            
            if score > 0:
                matches.append({
                    "item": data_item,
                    "score": score,
                    "matched_features": {
                        "name": score >= 3,
                        "color": score >= 2,
                        "material": score >= 1
                    }
                })
        
        # 점수순 정렬
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:3]  # 상위 3개만 반환
    
    def _find_outfit_matches(self, extracted_items: Dict) -> List[Dict]:
        """아웃핏 조합 매칭"""
        matches = []
        
        # 추출된 아이템들을 하나의 조합으로 만들기
        extracted_outfit = []
        if extracted_items["top"]["item"]:
            extracted_outfit.append(extracted_items["top"]["item"])
        if extracted_items["bottom"]["item"]:
            extracted_outfit.append(extracted_items["bottom"]["item"])
        if extracted_items["shoes"]["item"]:
            extracted_outfit.append(extracted_items["shoes"]["item"])
        
        for combo in self.fashion_reference_data["outfit_combinations"]:
            score = 0
            matched_items = []
            
            if isinstance(combo["items"], list):
                for extracted_item in extracted_outfit:
                    for combo_item in combo["items"]:
                        if extracted_item in combo_item or combo_item in extracted_item:
                            score += 1
                            matched_items.append(combo_item)
            
            if score > 0:
                matches.append({
                    "combo": combo,
                    "score": score,
                    "matched_items": matched_items
                })
        
        # 점수순 정렬
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:3]  # 상위 3개만 반환
    
    def _find_color_matches(self, extracted_items: Dict) -> List[Dict]:
        """컬러 매칭"""
        matches = []
        extracted_colors = []
        
        # 추출된 색상들 수집
        for section in ["top", "bottom", "shoes"]:
            if extracted_items[section]["color"]:
                extracted_colors.append(extracted_items[section]["color"])
        
        for color_data in self.fashion_reference_data["color_recommendations"]:
            score = 0
            
            for extracted_color in extracted_colors:
                if extracted_color in color_data.get("color", ""):
                    score += 1
            
            if score > 0:
                matches.append({
                    "color_data": color_data,
                    "score": score,
                    "matched_colors": extracted_colors
                })
        
        # 점수순 정렬
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:3]  # 상위 3개만 반환
    
    def _generate_recommendations_from_matching(self, matched_data: Dict, extracted_items: Dict = None) -> List[str]:
        """매칭 결과와 스타일링 방법을 바탕으로 추천 생성"""
        recommendations = []
        
        # 정확한 매칭이 있으면 추천
        if matched_data["exact_matches"]:
            recommendations.append("✅ 이미지의 아이템들이 패션 데이터와 정확히 매칭됩니다!")
        
        # 유사한 아웃핏 조합이 있으면 추천
        if matched_data["similar_matches"]:
            best_match = matched_data["similar_matches"][0]
            recommendations.append(f"🎯 유사한 아웃핏 조합: {best_match['combo']['combination']}")
        
        # 컬러 매칭이 있으면 추천
        if matched_data["color_matches"]:
            best_color = matched_data["color_matches"][0]
            recommendations.append(f"🎨 컬러 조합이 패션 데이터와 잘 맞습니다: {best_color['color_data']['color']}")
        
        # 스타일링 방법 기반 추천
        if extracted_items and "styling_methods" in extracted_items:
            styling = extracted_items["styling_methods"]
            
            # 상의 착용법 분석
            if styling.get("top_wearing_method"):
                method = styling["top_wearing_method"]
                if "완전히 넣" in method:
                    recommendations.append("👔 상의를 완전히 넣은 스타일링이 깔끔하고 정돈된 느낌을 줍니다!")
                elif "일부만 넣" in method:
                    recommendations.append("🎯 상의를 일부만 넣은 스타일링이 캐주얼하면서도 세련된 느낌을 줍니다!")
                elif "안 넣" in method:
                    recommendations.append("🆒 상의를 넣지 않은 스타일링이 편안하고 자연스러운 느낌을 줍니다!")
            
            # 핏감 분석
            if styling.get("fit_details"):
                fit = styling["fit_details"]
                if "타이트" in fit:
                    recommendations.append("💪 타이트한 핏감이 몸의 라인을 잘 살려줍니다!")
                elif "여유" in fit:
                    recommendations.append("😌 여유로운 핏감이 편안하고 트렌디한 느낌을 줍니다!")
            
            # 실루엣 밸런스 분석
            if styling.get("silhouette_balance"):
                balance = styling["silhouette_balance"]
                if "균형" in balance or "비율" in balance:
                    recommendations.append("⚖️ 상하의 길이 비율이 잘 맞아 전체적인 균형감이 좋습니다!")
            
            # 스타일링 포인트 분석
            if styling.get("styling_points"):
                points = styling["styling_points"]
                if "롤업" in points:
                    recommendations.append("🔄 소매 롤업이 캐주얼하면서도 세련된 포인트가 됩니다!")
                if "버튼" in points:
                    recommendations.append("🔘 버튼 스타일링이 정돈된 느낌을 줍니다!")
        
        # 개선 제안
        if not matched_data["exact_matches"]:
            recommendations.append("💡 이 룩을 더 개선하려면 비슷한 스타일의 다른 아이템들을 시도해보세요.")
        
        return recommendations
        