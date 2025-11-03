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
        
        # 여름 시즌 설정
        self.current_season = "summer"
        print(f"🌞 현재 시즌: {self.current_season} - 짧은 옷들만 추천")
        
        # 전문가별 특성 정의
        self.expert_profiles = {
            FashionExpertType.STYLE_ANALYST: {
                "role": "패션 스타일 분석 전문가",
                "expertise": "체형분석, 핏감분석, 실루엣",
                "focus": "사용자의 체형과 어울리는 스타일을 분석하고 핏감을 고려한 추천을 제공합니다.",
                # 개선된 프롬프트 - 반말 대화 스타일
                "prompt_template": """당신은 스타일 분석가입니다. 반말로 간결하게(2-3문장) 대화해주세요.

**필수 답변 형식:**
- 첫 문장: "색상+아이템에 색상+아이템이 잘 어울려" 형식으로 시작 (예: "네이비 반팔에 그레이 슬랙스가 잘 어울려")
- 조사 사용: "~에" 사용 ("~랑", "~과", "~하고" 금지)
- JSON 데이터의 실제 정보를 자연스럽게 활용

**금지 사항:**
- 감탄사로 시작 금지 ("야", "어", "오")
- 주관적 감탄 금지 ("완전 좋아", "너무 좋아")
- 고정 접두사 금지 ("💡 스타일링:", "🎯 적합한 상황:" 등)

예시: "네이비 반팔에 그레이 슬랙스가 잘 어울려. 클래식하면서도 세련된 느낌을 줘." """
            },
            FashionExpertType.TREND_EXPERT: {
                "role": "패션 트렌드 전문가",
                "expertise": "최신트렌드, 셀럽스타일",
                "focus": "최신 패션 트렌드, 인플루언서 스타일을 반영한 추천을 제공합니다.",
                # 개선된 프롬프트 - 반말 대화 스타일 + Pinterest 트렌드 데이터
                "prompt_template": """당신은 트렌드 전문가입니다. 반말로 간결하게(2-3문장) 대화해주세요.

**필수 답변 형식:**
- 첫 문장: "색상+아이템에 색상+아이템이 잘 어울려" 형식으로 시작
- 조사 사용: "~에" 사용 ("~랑", "~과", "~하고" 금지)
- Pinterest 데이터가 있으면 구체적 수치 언급 (예: "Pinterest에서 ~점으로")
- 현재 트렌드를 구체적으로 언급

**금지 사항:**
- 감탄사로 시작 금지 ("야", "어", "오")
- 주관적 감탄 금지 ("완전 좋아", "인기 끌 수 있을 걸")
- 고정 접두사 금지

예시: "네이비 반팔에 그레이 슬랙스가 잘 어울려. 올해 여름 미니멀 스타일 트렌드랑 딱 맞아." """
            },
            FashionExpertType.COLOR_EXPERT: {
                "role": "컬러 전문가",
                "expertise": "색상조합, 톤온톤, 퍼스널컬러", 
                "focus": "개인의 피부톤과 어울리는 색상 분석과 조화로운 컬러 조합을 제안합니다.",
                # 개선된 프롬프트 - 색감 조합 근거 중심 + 반말 스타일
                                    "prompt_template": """당신은 컬러 전문가입니다. 반말로 간결하게(2-3문장) 대화해주세요.

**필수 답변 형식:**
- 첫 문장: 색상명으로 시작해 색상 이론 언급 (예: "화이트와 베이지는 톤온톤 원리로 조화를 이뤄")
- 활용 가능한 색상 이론: 톤온톤, 명도 대비, 보색 관계, 색상 온도, 퍼스널컬러 등
- JSON 데이터의 실제 색상 정보를 사용

**금지 사항:**
- 주관적 감탄으로 시작 금지 ("이 조합 좋아", "그 옷 조합 괜찮아", "야", "완전 좋아")
- 추상적 표현 금지 ("~한 느낌", "~한 분위기", "일반적으로")
- 고정 접두사 금지

예시: "화이트 셔츠와 베이지 팬츠는 톤온톤 원리로 안정적인 조화를 만들어. 명도 대비도 적당해서 세련돼 보여." """
            },
            FashionExpertType.FITTING_COORDINATOR: {
                "role": "가상 피팅 코디네이터",
                "expertise": "피팅연동, 결과분석, 대안제시",
                "focus": "모든 전문가의 의견을 종합하여 최종 코디네이션을 완성합니다.",
                # 개선된 프롬프트 - 반말 대화 스타일
                "prompt_template": """당신은 피팅 코디네이터입니다. 반말로 간결하게(2-3문장) 대화해주세요.

**필수 답변 형식:**
- 첫 문장: "색상+아이템에 색상+아이템이 잘 어울려" 형식으로 시작
- 조사 사용: "~에" 사용 ("~랑", "~과", "~하고" 금지)
- 전문가들의 의견을 종합하여 균형잡힌 관점 제시
- JSON 데이터의 실제 정보를 자연스럽게 활용

**금지 사항:**
- 감탄사로 시작 금지 ("야", "어", "오")
- 주관적 감탄 금지 ("완전 좋아", "너무 좋아")
- 고정 접두사 금지 ("💡 스타일링:", "🎯 적합한 상황:" 등)

예시: "네이비 반팔에 그레이 슬랙스가 잘 어울려. 클래식하면서도 세련된 느낌을 줘." """
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
            
            # 아웃핏 조합 매칭 (화이트+화이트 제외, 상황별 가중치 적용)
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
                
                # 화이트+화이트 조합 제외 (상의/하의만 체크, 신발 제외)
                white_count = 0
                for item in items_list:
                    # 신발 관련 키워드가 포함된 아이템은 제외
                    if any(shoes_keyword in item.lower() for shoes_keyword in ['신발', '슈즈', '로퍼', '스니커', '부츠', '샌들', 'shoes', 'sneakers', 'loafers', 'boots']):
                        continue
                    if '화이트' in item.lower() or 'white' in item.lower():
                        white_count += 1
                if white_count >= 2:  # 상의/하의에서 화이트가 2개 이상이면 제외
                    continue
                
                # 상황별 가중치 계산
                weight = 1.0
                is_formal_occasion = any(keyword in user_keywords for keyword in ['소개팅', '데이트', '면접', '출근', '비즈니스'])
                is_sogeting = any(keyword in user_keywords for keyword in ['소개팅'])
                
                if is_formal_occasion:
                    # 소개팅/데이트 등에서는 셔츠, 니트 등에 가중치 부여 (남자 대상)
                    formal_items = ['셔츠', '니트', '가디건', '자켓', '코트']
                    has_formal_item = False
                    
                    for item in items_list:
                        if any(formal in item.lower() for formal in formal_items):
                            weight += 0.5  # 셔츠/니트 등에 가중치
                            has_formal_item = True
                            break
                    
                    # 소개팅에서는 셔츠/니트가 포함되지 않은 조합은 제외
                    if is_sogeting and not has_formal_item:
                        print(f"🚫 소개팅에서 제외: '{combo['combination']}' (포멀한 아이템 없음)")
                        continue
                    elif is_sogeting and has_formal_item:
                        print(f"✅ 소개팅에서 통과: '{combo['combination']}' (포멀한 아이템 포함)")
                    
                    # 소개팅에서는 캐주얼한 아이템 완전 제외
                    if is_sogeting:
                        casual_items = ['후드', '맨투맨', '반팔티', '티셔츠']
                        has_casual_item = False
                        for item in items_list:
                            if any(casual in item.lower() for casual in casual_items):
                                has_casual_item = True
                                print(f"🚫 소개팅에서 제외: '{combo['combination']}' (캐주얼 아이템: {item})")
                                break
                        if has_casual_item:
                            continue  # 이 조합 완전 제외
                    else:
                        # 데이트 등에서는 캐주얼한 아이템에 페널티만
                        casual_items = ['후드', '맨투맨', '반팔티', '티셔츠']
                        for item in items_list:
                            if any(casual in item.lower() for casual in casual_items):
                                weight -= 0.3  # 캐주얼 아이템에 페널티
                                break
                
                # 각 조건을 개별적으로 확인
                items_match = any(any(keyword in item.lower() for keyword in user_keywords) for item in items_list)
                occasion_match = any(keyword in occasion_str for keyword in user_keywords) if occasion_str else False
                
                # 디버깅: 매칭 과정 출력
                if user_keywords and any(keyword in ['소개팅', '데이트', '출근'] for keyword in user_keywords):
                    print(f"🔍 매칭 확인: '{combo['combination']}' (occasion: '{combo['occasion']}', weight: {weight:.1f})")
                    print(f"   user_keywords: {user_keywords}")
                    print(f"   occasion_str: '{occasion_str}'")
                    print(f"   occasion_match: {occasion_match}")
                    if occasion_match:
                        print(f"   ✅ 매칭 성공!")
                
                # 디버깅 출력
                if occasion_match:
                    print(f"🎯 매칭 발견: '{combo['combination']}' (occasion: '{combo['occasion']}', weight: {weight:.1f})")
                
                if items_match or occasion_match:
                    # 가중치를 포함하여 저장
                    combo_with_weight = combo.copy()
                    combo_with_weight['weight'] = weight
                    actual_combos.append(combo_with_weight)
            
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
                
                # 전문가별 선택이 실패한 경우 가중치 기반 우선순위
                if combo is None:
                    # 가중치가 높은 순으로 정렬
                    sorted_combos = sorted(actual_combos, key=lambda x: x.get('weight', 1.0), reverse=True)
                    
                    # 1순위: 가중치가 가장 높은 조합
                    if sorted_combos:
                        combo = sorted_combos[0]
                        # print(f"✅ 가중치 기반 선택: '{combo['combination']}' (weight: {combo.get('weight', 1.0):.1f})")
                    
                    # 2순위: occasion이 정확히 매칭되는 것
                    if combo is None:
                        for c in actual_combos:
                            if c.get('occasion') and any(keyword in c['occasion'].lower() for keyword in user_keywords):
                                combo = c
                                # print(f"✅ occasion 매칭으로 선택: '{c['combination']}' (occasion: '{c['occasion']}')")
                                break
                    
                    # 3순위: 첫 번째 조합 사용
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
        """JSON 데이터를 기반으로 LLM을 사용하여 자연스럽고 다양한 대화 스타일로 답변 생성"""
        
        # JSON 데이터가 없으면 기본 데이터 사용 (여름 시즌에 맞게, 다양한 색상 조합)
        if not json_data:
            import random
            
            # 단일 색상 조합 (아이템당 하나의 색상만, 상하의 다른 색만)
            color_combinations = [
                {"top": "네이비", "bottom": "베이지"},
                {"top": "블랙", "bottom": "베이지"},
                {"top": "그레이", "bottom": "네이비"},
                {"top": "베이지", "bottom": "네이비"},
                {"top": "화이트", "bottom": "네이비"},
                {"top": "화이트", "bottom": "블랙"},
                {"top": "카키", "bottom": "화이트"},
                {"top": "네이비", "bottom": "화이트"},
                {"top": "브라운", "bottom": "베이지"},
                {"top": "베이지", "bottom": "블랙"},
                {"top": "그레이", "bottom": "화이트"},
                {"top": "화이트", "bottom": "그레이"},
                {"top": "블랙", "bottom": "네이비"},
                {"top": "카키", "bottom": "블랙"},
                {"top": "브라운", "bottom": "네이비"}
            ]
            
            # 같은 색 조합 제거 (안전장치)
            valid_combinations = [combo for combo in color_combinations 
                                if combo["top"].lower() != combo["bottom"].lower()]
            
            # 하나의 조합만 선택 (여러 색상 추천 방지)
            selected_colors = random.choice(valid_combinations)
            
            # 소개팅/비즈니스 상황 체크
            formal_keywords = ["소개팅", "데이트", "면접", "출근", "비즈니스", "회사", "미팅", "회의", "오피스"]
            is_formal_occasion = any(keyword in user_input.lower() for keyword in formal_keywords)
            
            # 상황에 따른 상의 아이템 선택
            if is_formal_occasion:
                top_item = "반팔 셔츠"  # 소개팅/비즈니스에는 셔츠
                bottom_item = "슬랙스"   # 소개팅/비즈니스에는 슬랙스
                shoes_item = "로퍼"      # 소개팅/비즈니스에는 로퍼
                styling_methods = {
                    "top_wearing_method": "살짝 넣기",
                    "tuck_degree": "살짝 넣기",
                    "fit_details": "깔끔하고 정돈된 핏",
                    "silhouette_balance": "비즈니스에 적합한 실루엣",
                    "styling_points": "단추 위쪽 1-2개 해제, 소매 롤업"
                }
            else:
                top_item = "반팔 티셔츠"  # 캐주얼에는 티셔츠
                bottom_item = "반바지"    # 캐주얼에는 반바지
                shoes_item = "스니커즈"   # 캐주얼에는 스니커즈
                styling_methods = {
                    "top_wearing_method": "자연스럽게 내려놓기",
                    "tuck_degree": "자유롭게 내려놓기",
                    "fit_details": "시원하고 가벼운 핏",
                    "silhouette_balance": "여름에 적합한 짧은 실루엣",
                    "styling_points": "시원한 소재, 가벼운 느낌"
                }
            
            json_data = {
                "top": {"item": top_item, "color": selected_colors["top"], "fit": "레귤러핏", "material": "면"},
                "bottom": {"item": bottom_item, "color": selected_colors["bottom"], "fit": "레귤러핏", "material": "면"},
                "shoes": {"item": shoes_item, "color": "화이트", "style": "캐주얼"},
                "styling_methods": styling_methods
            }
        
        # 전문가 프로필 가져오기
        expert_profile = self.expert_profiles.get(expert_type, self.expert_profiles[FashionExpertType.STYLE_ANALYST])
        
        # 시스템 프롬프트 구성 (구체적인 옷 조합 정보 강조)
        system_prompt = f"""당신은 {expert_profile['role']}입니다. {expert_profile['focus']}

**🚨 응답 시작 강제 규칙 (절대 위반 금지):**
- 첫 문장은 무조건 구체적인 옷 조합으로 시작해야 함
- "{json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')}에 {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')}가 잘 어울려" 같은 형태로 시작
- "이 옷 조합 좋아", "그 옷 조합 좋아", "저 옷 조합 좋아" 같은 주관적 표현 절대 금지
- 주관적 판단, 감탄사, 추상적 설명 절대 금지
- 바로 구체적인 옷 조합 분석으로 시작해야 함

**🔥 핵심 원칙: 첫 문장은 반드시 구체적인 옷 조합으로 시작!**
- 첫 문장은 무조건 "{json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')}에 {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')}가 잘 어울려" 같은 형태로 시작
- 주관적 판단, 감탄사, 추상적 설명 절대 금지
- 바로 구체적인 옷 조합 분석으로 시작해야 함

**🚨 절대 금지: 첫 문장에서 주관적 뉘앙스 표현**
- "이 조합 좋아", "그 조합 좋아", "저 조합 좋아" (가장 중요한 금지)
- "이 조합이 딱이네", "그 옷 조합이 딱이야", "진짜 좋아", "너무 좋아", "완전 좋아"
- "그 옷 조합 괜찮아", "이 옷 조합 괜찮아", "저 옷 조합 괜찮아"
- "야", "어", "오" 같은 감탄사 (특히 "야"는 절대 금지)
- "이 옷 조합", "이런 조합", "그 옷 조합" 같은 주관적 표현
- "피부톤이랑 잘 어울리는 색이라" 같은 막연한 설명
- "세련되면서도 깔끔한 느낌 나" 같은 주관적 판단
- "정말 멋질 거 같아" 같은 감탄 표현
- "캐주얼하면서도 클래식한 스타일이 될 거야" 같은 추상적 표현
- "자신감 있게 입고 나갈 수 있을 거 같네" 같은 주관적 판단
- "피부톤에 따라 다르겠지만" 같은 조건부 설명
- "대체로", "일반적으로", "보통" 같은 추상적 표현
- 모든 감탄사나 주관적 판단으로 시작하는 문장
- "이렇게 입으면" 같은 추상적 표현
- "딱이야", "완벽해", "좋아", "괜찮아" 같은 감탄 표현
- "딱일 거 같아", "좋을 거 같아" 같은 추측 표현
- "~는 깔끔하고 세련된 느낌 주고", "~는 여름 분위기 물씬 나" 같은 막연한 설명
- "~는 ~한 느낌", "~는 ~한 분위기" 같은 추상적 표현
- "잘 어울려", "좋아 보여", "멋있어 보여" 같은 주관적 판단
- "피부톤에 잘 맞는 중성적인 컬러라" 같은 막연한 설명
- "편하게 입을 수 있을 거야" 같은 추상적 표현
- "깔끔하고 세련된 느낌 낼 수 있어" 같은 주관적 판단
- "편하면서도 깔끔한 느낌이 들 거야" 같은 막연한 설명
- "피부톤에 잘 맞는 색감이라 화사해 보일 거고" 같은 주관적 판단
- "캐주얼한 무드가 살아날 거 같아" 같은 추상적 표현
- "소개팅 가는데 딱이네" 같은 주관적 판단

**✅ 올바른 시작 예시 (반드시 이 형태로 시작):**
- "{json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')}랑 {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')}가 잘 어울려"
- "{json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')}와 {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')} 조합은 색상 대비가..."
- "{json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')}에 {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')}를 매치하면..."

**구체적인 옷 조합 정보:**
- 상의: {json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')} ({json_data.get('top', {}).get('fit', '')})
- 하의: {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')} ({json_data.get('bottom', {}).get('fit', '')})
- 신발: {json_data.get('shoes', {}).get('color', '')} {json_data.get('shoes', {}).get('item', '')}
- 스타일링: {json_data.get('styling_methods', {}).get('styling_points', '')}

**반말 대화 스타일 (무조건 반말 사용):**
- 친구처럼 편안하고 자연스럽게 반말로 대화
- "야", "어", "오" 같은 감탄사나 친근한 호칭으로 시작하지 않기
- 하드코딩된 템플릿이나 고정된 문구 사용 금지
- 다양한 표현과 어조 사용 (감탄, 걱정, 확신, 제안 등)
- 상황에 따라 다른 반응 (칭찬, 조언, 질문 등)
- 문장 구조를 다양하게 변화시키기
- 자연스러운 연결어와 전환어 사용

**중요한 규칙:**
1. 반드시 위의 구체적인 옷 조합 정보를 자연스럽게 문장에 포함시키기
2. 여름 시즌에 맞는 시원한 소재의 옷들만 추천
3. 하드코딩된 예시 문장을 그대로 사용하지 말고, 창의적이고 자연스러운 표현으로 응답하기
4. "💡 스타일링:", "🎯 적합한 상황:", "✨ 스타일링:", "🎨 스타일리스트 조언:" 같은 고정된 접두사 사용 금지
5. 스타일링 정보는 자연스럽게 문장에 녹여내기
6. 무조건 반말로 응답하기 (존댓말 사용 금지)
7. 간결하고 핵심적인 내용만 전달하기 (불필요한 설명 제거)
8. 다양한 감정과 어조로 대화하기
9. **절대 중요: 하나의 아이템당 하나의 색상만 추천하기 (여러 색상 나열 금지)**
10. "카키, 화이트 재킷"이나 "브라운, 블루 슬랙스" 같은 여러 색상 나열 절대 금지
11. 반드시 단일 색상으로만 추천: "카키 재킷", "브라운 슬랙스" 형태로만 사용
12. "~, ~ 색상", "~나 ~ 색상" 같은 여러 색상 제시 절대 금지
13. **넥타이 언급 절대 금지**: 넥타이, 타이 등 모든 관련 표현 사용 금지
14. **"정장" 표현 금지**: "정장스러운", "정장적인", "정장느낌" 등 모든 정장 관련 표현 대신 "포멀한" 사용
15. **체크무늬/패턴 언급 절대 금지**: 체크무늬, 체크, 체크 패턴 등 모든 관련 표현 사용 금지, 단색만 추천
16. **남성 패션에 부적절한 표현 금지**: "여성스러운", "여성적인", "귀여운" 등의 표현 대신 "세련된", "우아한", "깔끔한" 사용
17. **같은 색 상하의 조합 절대 금지**: 상의와 하의가 같은 색인 조합 금지 (예: 블랙 셔츠 + 블랙 바지), 반드시 다른 색 조합만 추천
18. **중복 문장 절대 금지**: 같은 문장이나 비슷한 내용을 반복하지 말고, 한 번만 명확하게 표현
19. **핏 정보 필수**: 모든 옷에 핏 정보 포함, 핏 정보가 없으면 와이드핏으로 추천 (예: "화이트 와이드 셔츠", "블랙 와이드 슬랙스")
20. **주머니 관련 표현 절대 금지**: "주머니에 손 넣어서", "포켓에 손 넣고" 등 주머니/포켓 활용 언급 금지

**사용자 입력:**
{user_input}

위의 구체적인 옷 조합 정보를 바탕으로 간결하고 핵심적인 패션 조언을 제공해주세요. 반드시 응답 시작 부분에 추천하는 옷 조합을 명확하게 명시하고, 반말로 간결하게 응답해주세요."""
        
        # 사용자 프롬프트 (구체적인 옷 조합 강조)
        user_prompt = f"이 {json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')} + {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')} 조합에 대해 {expert_profile['role']}의 관점에서 반말로 간결하게 조언해주세요. 반드시 첫 문장은 '{json_data.get('top', {}).get('color', '')} {json_data.get('top', {}).get('item', '')}에 {json_data.get('bottom', {}).get('color', '')} {json_data.get('bottom', {}).get('item', '')}가 잘 어울려' 같은 형태로 시작하고, 실제 옷 정보를 명확하게 언급해주세요."
        
        try:
            # LLM 호출
            response = await self._call_openai_async(system_prompt, user_prompt)
            
            # 응답 시작 부분 강제 수정 (가장 먼저 적용)
            response = self._force_correct_response_start(response, json_data)
            
            # 여성 전용 아이템 필터링 적용
            response = self._filter_female_only_items(response, json_data)
            
            # 여름 시즌 필터링 적용
            response = self._filter_for_summer_season(response, json_data)
            
            # 소개팅/비즈니스 상황 필터링 적용
            response = self._filter_for_formal_occasion(response, json_data, user_input)
            
            # 여러 색상 나열 방지 필터링 적용
            response = self._filter_multiple_colors(response)
            
            # 넥타이 및 정장 관련 표현 제거
            response = self._filter_unwanted_items(response)
            
            # 같은 색 조합 방지 필터링
            response = self._filter_same_color_combinations(response, json_data)
            
            # 중복 응답 및 핏 정보 추가 필터링
            response = self._filter_duplicate_and_add_fit(response)
            
            # 상황별 필터링 및 용어 개선
            response = self._improve_response_for_occasion(response, user_input)
            
            # 어려운 용어 제거 필터링
            response = self._remove_difficult_terms(response)
            
            return response
            
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            # LLM 호출 실패 시 기본 응답 반환
            return f"죄송합니다. 현재 응답을 생성할 수 없습니다. (오류: {str(e)})"

    def _filter_for_summer_season(self, response: str, json_data: dict) -> str:
        """여름 시즌에 맞는 짧은 옷들만 추천하도록 필터링"""
        if self.current_season != "summer":
            return response
        
        # 여름에 부적합한 긴 옷들 체크
        summer_inappropriate_items = [
            "긴팔", "롱슬리브", "긴바지", "롱팬츠", 
            "코트", "패딩", "니트", "스웨터", "가디건", "블레이저"
        ]
        
        # JSON 데이터에서 아이템 확인
        top_item = json_data.get("top", {}).get("item", "").lower()
        bottom_item = json_data.get("bottom", {}).get("item", "").lower()
        top_color = json_data.get("top", {}).get("color", "").lower()
        bottom_color = json_data.get("bottom", {}).get("color", "").lower()
        
        # 화이트+화이트 조합 체크 및 수정
        if top_color == "화이트" and bottom_color == "화이트":
            # 화이트+화이트 조합을 다른 색상으로 변경
            color_alternatives = ["베이지", "네이비", "그레이", "블랙", "카키"]
            import random
            new_color = random.choice(color_alternatives)
            
            # 응답에서 색상 교체
            response = response.replace("화이트", new_color, 1)  # 첫 번째 화이트만 교체
            response = response.replace("화이트", new_color, 1)  # 두 번째 화이트도 교체
            
            # 색상 변경 이유 설명 추가 (더 자연스럽게)
            color_change_phrases = [
                f" 화이트+화이트는 너무 단조로워서 {new_color}로 바꿨어!",
                f" 화이트+화이트보다는 {new_color}가 더 멋있을 거야!",
                f" {new_color}로 바꾸면 더 세련될 거야!",
                f" {new_color}가 더 잘 어울릴 것 같아!"
            ]
            import random
            response += random.choice(color_change_phrases)
        
        # 여름에 부적합한 아이템이 포함되어 있으면 수정
        has_inappropriate_item = any(item in top_item for item in summer_inappropriate_items) or \
                               any(item in bottom_item for item in summer_inappropriate_items)
        
        if has_inappropriate_item:
            # 여름에 적합한 대체 아이템으로 수정
            summer_alternatives = {
                "긴팔": "반팔",
                "롱슬리브": "반팔", 
                "긴바지": "반바지",
                "롱팬츠": "반바지",
                "코트": "반팔",
                "패딩": "반팔",
                "니트": "반팔",
                "스웨터": "반팔",
                "가디건": "반팔",
                "블레이저": "반팔"
            }
            
            # 응답에서 부적합한 아이템을 여름에 적합한 아이템으로 교체
            for inappropriate, appropriate in summer_alternatives.items():
                if inappropriate in response:
                    response = response.replace(inappropriate, appropriate)
            
            # 여름 시즌 강조 문구 추가 (더 자연스럽게)
            summer_phrases = [
                " 여름에 딱 맞는 시원한 조합이야!",
                " 여름에 완벽한 조합이네!",
                " 여름에 시원하고 좋아!",
                " 여름에 딱이야!"
            ]
            import random
            response += random.choice(summer_phrases)
        
        return response

    def _filter_for_formal_occasion(self, response: str, json_data: dict, user_input: str) -> str:
        """소개팅/비즈니스 상황에서는 자켓+반바지 조합을 엄격하게 제외"""
        # 소개팅/비즈니스 상황 체크
        formal_keywords = ["소개팅", "데이트", "면접", "출근", "비즈니스", "회사", "미팅", "회의", "오피스"]
        is_formal_occasion = any(keyword in user_input.lower() for keyword in formal_keywords)
        
        if not is_formal_occasion:
            return response
        
        # JSON 데이터에서 아이템 확인
        top_item = json_data.get("top", {}).get("item", "").lower()
        bottom_item = json_data.get("bottom", {}).get("item", "").lower()
        
        # 자켓+반바지 조합 체크
        jacket_keywords = ["자켓", "재킷", "블레이저", "블레이져", "재킷"]
        shorts_keywords = ["반바지", "쇼츠", "하프팬츠", "숏팬츠", "숏츠", "쇼트팬츠"]
        
        has_jacket = any(k in top_item for k in jacket_keywords)
        has_shorts = any(k in bottom_item for k in shorts_keywords)
        
        # 자켓이 있으면 완전히 제외 (여름 시즌 + 소개팅 부적절)
        if has_jacket:
            return "죄송해, 소개팅에는 자켓이 부적절해. 다른 착장을 추천해줄게!"
        
        # 반바지가 있으면 완전히 제외
        if has_shorts:
            return "죄송해, 소개팅에는 반바지가 부적절해. 긴 바지를 추천해줄게!"
        
        # 부적절한 신발 체크
        shoes_item = json_data.get("shoes", {}).get("item", "").lower()
        inappropriate_shoes = ["덩크", "스니커즈", "운동화", "캔버스", "컨버스"]
        has_inappropriate_shoes = any(k in shoes_item for k in inappropriate_shoes)
        
        if has_inappropriate_shoes:
            return "죄송해, 소개팅에는 운동화가 부적절해. 구두나 로퍼를 추천해줄게!"
        
        # 캐주얼한 아이템들을 포멀한 아이템으로 교체
        casual_to_formal = {
            "티셔츠": ["반팔 셔츠", "반팔 폴로", "반팔 니트"],
            "그래픽": ["단색", "스트라이프", "체크"],
            "오버사이즈": ["레귤러핏", "슬림핏"],
            "와이드": ["레귤러핏", "슬림핏"],
            "맨투맨": ["반팔 셔츠"],
            "후드티": ["반팔 셔츠"],
            "크롭": ["반팔 셔츠"]
        }
        
        # 캐주얼한 아이템이 있으면 포멀한 아이템으로 교체
        for casual_item, formal_alternatives in casual_to_formal.items():
            if casual_item in top_item:
                import random
                new_item = random.choice(formal_alternatives)
                
                # 응답에서 아이템 교체
                if casual_item == "그래픽":
                    response = response.replace("그래픽", new_item)
                elif casual_item == "오버사이즈":
                    response = response.replace("오버사이즈", new_item)
                elif casual_item == "와이드":
                    response = response.replace("와이드", new_item)
                elif casual_item == "티셔츠":
                    response = response.replace("티셔츠", new_item.split()[-1])
                elif casual_item in ["맨투맨", "후드티", "크롭"]:
                    response = response.replace(casual_item, new_item.split()[-1])
                
                # 교체 이유 설명 추가
                response += f" 소개팅에는 {new_item}가 더 적합해!"
                break  # 첫 번째 매칭되는 아이템만 교체
        
        return response

    def _filter_multiple_colors(self, response: str) -> str:
        """여러 색상 나열을 단일 색상으로 변경하는 강화된 필터"""
        import re
        
        print(f"🔍 필터링 전: {response}")
        
        # 1단계: 색상 중복 제거 (예: "블랙 블랙" -> "블랙")
        color_names = ['화이트', '블랙', '네이비', '베이지', '그레이', '브라운', '카키', '블루', '그린', '옐로우', '핑크', '퍼플']
        for color in color_names:
            # 같은 색상이 연속으로 반복되는 경우 제거
            response = re.sub(f'{color}\\s+{color}', color, response)
        
        # 2단계: 여러 색상이 나열된 패턴들을 찾아서 첫 번째 색상만 남기기
        multiple_color_patterns = [
            # "화이트, 블랙 화이트 버튼다운 셔츠" -> "화이트 버튼다운 셔츠"
            (r'([가-힣]+),\s*([가-힣]+)\s+([가-힣]+)\s+(버튼다운|반팔|긴팔|폴로|니트|스웨터)\s*(셔츠|티셔츠)', r'\1 \4 \5'),
            # "화이트, 블랙 셔츠" -> "화이트 셔츠"
            (r'([가-힣]+),\s*([가-힣]+)\s+(셔츠|블라우스|가디건|코트|자켓|재킷|티셔츠|폴로|니트|스웨터)', r'\1 \3'),
            # "브라운, 블루 슬랙스" -> "브라운 슬랙스"  
            (r'([가-힣]+),\s*([가-힣]+)\s+(슬랙스|팬츠|바지|치노|데님|트라우저)', r'\1 \3'),
            # "화이트, 베이지 신발" -> "화이트 신발"
            (r'([가-힣]+),\s*([가-힣]+)\s+(신발|로퍼|스니커즈|구두|부츠|샌들)', r'\1 \3'),
            # "카키나 화이트 재킷" -> "카키 재킷"
            (r'([가-힣]+)나\s+([가-힣]+)\s+(재킷|셔츠|블라우스|가디건|코트|자켓)', r'\1 \3'),
            # "브라운이나 블루 슬랙스" -> "브라운 슬랙스"
            (r'([가-힣]+)이나\s+([가-힣]+)\s+(슬랙스|팬츠|바지|치노|데님)', r'\1 \3'),
            # "화이트 또는 베이지 셔츠" -> "화이트 셔츠"
            (r'([가-힣]+)\s+또는\s+([가-힣]+)\s+(재킷|셔츠|블라우스|가디건|코트|자켓)', r'\1 \3'),
            # "블랙/네이비 팬츠" -> "블랙 팬츠"
            (r'([가-힣]+)/([가-힣]+)\s+(슬랙스|팬츠|바지|치노|데님)', r'\1 \3'),
            # "블랙 반팔와" -> "블랙 반팔과"
            (r'([가-힣]+\s+[가-힣]+)와', r'\1과'),
        ]
        
        for pattern, replacement in multiple_color_patterns:
            old_response = response
            response = re.sub(pattern, replacement, response)
            if old_response != response:
                print(f"🔄 패턴 매칭: {pattern} -> {replacement}")
        
        # 3단계: 문장 구조 정리
        # "화이트 버튼다운 셔츠 + 블랙 반팔에" -> "화이트 버튼다운 셔츠에"  
        response = re.sub(r'([가-힣\s]+)\s*\+\s*([가-힣\s]+)에', r'\1에', response)
        
        # 4단계: 최종 정리 - 아이템 조합을 단순화
        # 복잡한 조합을 단순한 조합으로 변경
        if '화이트' in response and '블랙' in response:
            # 화이트와 블랙이 함께 나오면 화이트 우선
            response = re.sub(r'화이트[^\.]+블랙[^\.]+', 
                            '화이트 셔츠에 블랙 슬랙스가', response)
        
        print(f"🎨 여러 색상 필터링 적용 완료: {response}")
        return response

    def _filter_unwanted_items(self, response: str) -> str:
        """넥타이, 체크무늬, 부적절한 표현들을 제거하는 필터"""
        import re
        
        print(f"🚫 불필요한 아이템 필터링 전: {response}")
        
        # 1. 넥타이 관련 표현 완전 제거
        necktie_patterns = [
            r'넥타이[를을이가와과에]?\s*[가-힣]*\s*',
            r'타이[를을이가와과에]?\s*[가-힣]*\s*',
            r'넥타이\s*착용[하해]?\s*[가-힣]*\s*',
            r'넥타이\s*매[고는다면]\s*',
            r'넥타이\s*없이\s*',
            r'넥타이\s*추가[하해]?\s*[가-힣]*\s*'
        ]
        
        for pattern in necktie_patterns:
            response = re.sub(pattern, '', response)
        
        # 2. 체크무늬 관련 표현을 단색으로 변경
        check_pattern_replacements = {
            '블루 체크무늬': '블루',
            '블랙 체크무늬': '블랙',
            '화이트 체크무늬': '화이트',
            '네이비 체크무늬': '네이비',
            '그레이 체크무늬': '그레이',
            '베이지 체크무늬': '베이지',
            '브라운 체크무늬': '브라운',
            '카키 체크무늬': '카키',
            '체크무늬': '',
            '체크': '',
            '체크 패턴': '',
            '체크 셔츠': '셔츠',
            '체크 반팔': '반팔',
            '체크무늬 셔츠': '셔츠',
            '체크무늬 반팔': '반팔',
            '깅엄체크': '',
            '타탄체크': '',
            '윈도체크': ''
        }
        
        for old_term, new_term in check_pattern_replacements.items():
            if old_term in response:
                response = response.replace(old_term, new_term)
                print(f"🔄 체크무늬 제거: '{old_term}' → '{new_term}'")
        
        # 3. 정장 관련 표현을 포멀한 표현으로 변경
        formal_replacements = {
            '정장스러운': '포멀한',
            '정장적인': '포멀한', 
            '정장느낌': '포멀한 느낌',
            '정장 느낌': '포멀한 느낌',
            '정장같은': '포멀한',
            '정장적': '포멀한',
            '정장스럽게': '포멀하게',
            '정장 스타일': '포멀한 스타일',
            '정장스타일': '포멀한 스타일',
            '정장 룩': '포멀한 룩',
            '정장룩': '포멀한 룩',
            '정장 분위기': '포멀한 분위기',
            '정장분위기': '포멀한 분위기'
        }
        
        for old_term, new_term in formal_replacements.items():
            if old_term in response:
                response = response.replace(old_term, new_term)
                print(f"🔄 정장 표현 변경: '{old_term}' → '{new_term}'")
        
        # 4. 남성 패션에 부적절한 표현들 제거
        inappropriate_expressions = {
            '여성스러운 느낌': '세련된 느낌',
            '여성스러운': '세련된',
            '여성적인 느낌': '우아한 느낌',
            '여성적인': '우아한',
            '여자같은': '세련된',
            '귀여운 느낌': '깔끔한 느낌',
            '귀엽게': '깔끔하게'
        }
        
        # 5. 주머니 관련 표현 제거
        pocket_expressions = [
            r'주머니에\s*손[을을이가]?\s*[넣살짝]*[어서서]?[서]?',
            r'포켓에\s*손[을을이가]?\s*[넣살짝]*[어서서]?[서]?', 
            r'주머니\s*활용[해하해서면]?',
            r'주머니\s*사용[해하해서면]?',
            r'손[을을이가]?\s*주머니에',
            r'손[을을이가]?\s*포켓에'
        ]
        
        for old_term, new_term in inappropriate_expressions.items():
            if old_term in response:
                response = response.replace(old_term, new_term)
                print(f"🔄 부적절한 표현 변경: '{old_term}' → '{new_term}'")
        
        # 주머니 관련 표현 제거
        for pattern in pocket_expressions:
            old_response = response
            response = re.sub(pattern, '', response)
            if old_response != response:
                print(f"🔄 주머니 표현 제거: {pattern} 패턴 적용됨")
        
        # 5. 연속된 공백 정리
        response = re.sub(r'\s+', ' ', response)
        
        print(f"✅ 불필요한 아이템 필터링 완료: {response}")
        return response

    def _filter_same_color_combinations(self, response: str, json_data: dict) -> str:
        """같은 색 상하의 조합을 다른 색 조합으로 변경하는 필터"""
        import re
        
        print(f"🎨 같은 색 조합 필터링 전: {response}")
        
        # 같은 색 상하의 조합 패턴 감지 (더 정확한 패턴 매칭)
        same_color_patterns = [
            # "화이트 린넨 반팔 셔츠에 화이트 와이드 슬랙스" 패턴
            (r'화이트\s+([가-힣\s]+)에\s+화이트\s+([가-힣\s]+)가', r'화이트 \1에 네이비 \2가'),
            # "블랙 셔츠에 블랙 슬랙스" 패턴
            (r'블랙\s+([가-힣\s]+)에\s+블랙\s+([가-힣\s]+)가', r'블랙 \1에 베이지 \2가'),
            # "네이비 셔츠에 네이비 바지" 패턴
            (r'네이비\s+([가-힣\s]+)에\s+네이비\s+([가-힣\s]+)가', r'네이비 \1에 화이트 \2가'),
            # "그레이 상의에 그레이 하의" 패턴
            (r'그레이\s+([가-힣\s]+)에\s+그레이\s+([가-힣\s]+)가', r'그레이 \1에 네이비 \2가'),
            # "베이지 셔츠에 베이지 팬츠" 패턴
            (r'베이지\s+([가-힣\s]+)에\s+베이지\s+([가-힣\s]+)가', r'베이지 \1에 네이비 \2가'),
            # "브라운 상의에 브라운 하의" 패턴
            (r'브라운\s+([가-힣\s]+)에\s+브라운\s+([가-힣\s]+)가', r'브라운 \1에 베이지 \2가'),
            # "카키 셔츠에 카키 바지" 패턴
            (r'카키\s+([가-힣\s]+)에\s+카키\s+([가-힣\s]+)가', r'카키 \1에 화이트 \2가'),
            # 일반적인 같은 색 패턴 (백업)
            (r'([가-힣]+)\s+([가-힣\s]+)에\s+\1\s+([가-힣\s]+)가', r'\1 \2에 베이지 \3가')
        ]
        
        # 대체 색상 매핑 (상의 색상 → 추천 하의 색상)
        color_alternatives = {
            '화이트': ['네이비', '블랙', '그레이'],
            '블랙': ['베이지', '화이트', '그레이'],
            '네이비': ['베이지', '화이트', '그레이'],
            '그레이': ['네이비', '화이트', '베이지'],
            '베이지': ['네이비', '블랙', '그레이'],
            '브라운': ['베이지', '네이비', '화이트'],
            '카키': ['화이트', '베이지', '네이비']
        }
        
        original_response = response
        
        # 패턴 매칭으로 같은 색 조합 수정
        for pattern, replacement in same_color_patterns:
            old_response = response
            response = re.sub(pattern, replacement, response)
            if old_response != response:
                print(f"🔄 같은 색 조합 수정: {pattern} → {replacement}")
        
        # JSON 데이터에서 상하의 색상 확인 및 수정
        if json_data:
            top_color = json_data.get('top', {}).get('color', '').lower()
            bottom_color = json_data.get('bottom', {}).get('color', '').lower()
            
            if top_color and bottom_color and top_color == bottom_color:
                # 같은 색이면 하의 색상을 다른 색으로 변경
                if top_color in color_alternatives:
                    import random
                    new_bottom_color = random.choice(color_alternatives[top_color])
                    
                    # JSON 데이터 업데이트
                    json_data['bottom']['color'] = new_bottom_color
                    
                    # 응답에서도 해당 색상 변경
                    color_pattern = f"{top_color}\\s+([가-힣]+)에\\s+{bottom_color}\\s+([가-힣]+)"
                    color_replacement = f"{top_color} \\1에 {new_bottom_color} \\2"
                    response = re.sub(color_pattern, color_replacement, response, flags=re.IGNORECASE)
                    
                    print(f"🔄 JSON 데이터 기반 색상 수정: {top_color} → {new_bottom_color}")
        
        if original_response != response:
            print(f"✅ 같은 색 조합 필터링 완료: {response[:100]}...")
        else:
            print(f"✅ 같은 색 조합 없음: 필터링 패스")
        
        return response

    def _remove_difficult_terms(self, response: str) -> str:
        """어려운 용어를 쉬운 용어로 변경하는 필터"""
        import re
        
        print(f"📚 어려운 용어 제거 전: {response}")
        
        # 어려운 용어 → 쉬운 용어 매핑
        difficult_terms = {
            "코듀로이": "면",
            "덴임": "면",
            "린넨": "면",
            "캐시미어": "니트",
            "알파카": "니트",
            "모헤어": "니트",
            "실크": "면",
            "레이온": "면",
            "폴리에스터": "면",
            "스팽덱스": "면",
            "엘라스테인": "면",
            "바시티": "면",
            "옥스포드": "면",
            "팝린": "면",
            "트위드": "면",
            "헤링본": "면",
            "체크": "무늬",
            "스트라이프": "줄무늬",
            "도트": "점무늬",
            "플라워": "꽃무늬",
            "지그재그": "지그재그무늬",
            "하운드스투스": "무늬",
            "윈도우펜": "무늬",
            "글렌체크": "무늬",
            "타탄": "무늬",
            "플리츠": "주름",
            "드레이프": "주름",
            "실루엣": "형태",
            "퍼스널 컬러": "나에게 맞는 색상",
            "톤온톤": "같은 색상 계열",
            "모노톤": "한 가지 색상",
            "핏감": "핏"
        }
        
        original_response = response
        
        # 어려운 용어를 쉬운 용어로 변경
        for difficult, easy in difficult_terms.items():
            response = response.replace(difficult, easy)
        
        if original_response != response:
            print(f"✅ 어려운 용어 제거 완료: {response[:100]}...")
        else:
            print(f"✅ 어려운 용어 없음: 필터링 패스")
        
        return response

    def _filter_duplicate_and_add_fit(self, response: str) -> str:
        """중복 문장 제거 및 핏 정보 추가하는 필터"""
        import re
        
        print(f"🔧 중복 제거 및 핏 추가 전: {response}")
        
        # 1. 중복 문장 제거
        # "화이트 셔츠에 블랙 슬랙스가. 화이트 셔츠에 블랙 슬랙스가." 같은 패턴
        sentences = response.split('.')
        unique_sentences = []
        seen_sentences = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in seen_sentences:
                unique_sentences.append(sentence)
                seen_sentences.add(sentence)
        
        response = '. '.join(unique_sentences)
        if response and not response.endswith('.'):
            response += '.'
        
        # 2. 핏 정보 추가 (색상 다음에 바로 옷이 나오면 와이드 핏 추가)
        # 단순하고 확실한 방법으로 교체
        clothing_items = ['셔츠', '티셔츠', '폴로', '니트', '스웨터', '블라우스', '가디건', '반팔', '긴팔', 
                         '슬랙스', '팬츠', '바지', '치노', '데님', '트라우저', '반바지', 
                         '재킷', '자켓', '코트', '블레이저']
        
        colors = ['화이트', '블랙', '네이비', '베이지', '그레이', '브라운', '카키', '블루', '그린']
        
        for color in colors:
            for item in clothing_items:
                # "색상 아이템" -> "색상 와이드 아이템" (해당 패턴에 핏 정보가 없는 경우만)
                pattern = f"{color} {item}"
                replacement = f"{color} 와이드 {item}"
                
                # 해당 패턴이 있고, 그 앞뒤에 핏 정보가 없는지 확인
                if pattern in response:
                    # 해당 패턴 주변에 핏 정보가 있는지 체크
                    pattern_with_fit = f"{color} (와이드|슬림|레귤러|오버|타이트) {item}"
                    if not re.search(pattern_with_fit, response):
                        response = response.replace(pattern, replacement)
                        print(f"🔄 핏 정보 추가: '{pattern}' -> '{replacement}'")
        
        print(f"✅ 중복 제거 및 핏 추가 완료: {response}")
        return response

    def _filter_female_only_items(self, response: str, json_data: dict) -> str:
        """여성 전용 아이템이 포함된 응답 필터링"""
        # 여성 전용 아이템 목록
        female_only_items = [
            "스커트", "드레스", "블라우스", "미디", "미니", "맥시", "원피스",
            "플리츠", "주름", "리본", "레이스", "프릴", "볼륨", "플레어",
            "A라인", "H라인", "X라인", "Y라인", "I라인", "O라인",
            "펌프스", "힐", "웨지", "플랫폼", "스틸레토", "메리제인",
            "크롭", "캐미솔", "탑", "튜브탑", "할리톱", "오프숄더",
            "원숄더", "스트랩리스", "백리스", "키홀", "컷아웃", "하프팬츠", "스키니", "숏팬츠"
        ]
        
        # JSON 데이터에서 여성 전용 아이템 체크
        for category, item_info in json_data.items():
            if isinstance(item_info, dict):
                item_name = item_info.get('item', '').lower()
                item_style = item_info.get('style', '').lower()
                item_fit = item_info.get('fit', '').lower()
                
                all_item_text = f"{item_name} {item_style} {item_fit}".lower().replace(" ", "")
                
                for female_item in female_only_items:
                    if female_item in all_item_text:
                        print(f"🚫 여성 전용 아이템 발견: {female_item} in {category}")
                        # 여성 전용 아이템을 남성용으로 대체
                        male_alternatives = {
                            "스커트": "슬랙스",
                            "드레스": "포멀한 셔츠",
                            "블라우스": "셔츠",
                            "미디": "일반",
                            "미니": "일반",
                            "맥시": "일반",
                            "원피스": "포멀한 셔츠",
                            "A라인": "일반",
                            "펌프스": "로퍼",
                            "힐": "로퍼",
                            "크롭": "반팔",
                            "탑": "반팔",
                            "하프팬츠": "슬랙스",
                            "스키니": "레귤러",
                            "숏팬츠": "슬랙스"
                        }
                        
                        if female_item in male_alternatives:
                            replacement = male_alternatives[female_item]
                            response = response.replace(female_item, replacement)
                            print(f"✅ {female_item} → {replacement}로 대체")
                        else:
                            # 대체할 수 없는 경우 기본값으로 대체
                            response = response.replace(female_item, "일반")
                            print(f"✅ {female_item} → 일반으로 대체")
        
        return response

    def _force_correct_response_start(self, response: str, json_data: dict) -> str:
        """응답 시작 부분을 강제로 올바른 형태로 수정 (강화된 버전)"""
        try:
            print(f"🔍 응답 시작 수정 전: {response[:150]}...")
            
            # 금지된 시작 패턴들 (더 강화)
            forbidden_starts = [
                "이 옷 조합 좋아", "그 옷 조합 좋아", "저 옷 조합 좋아",
                "이 조합 좋아", "그 조합 좋아", "저 조합 좋아",
                "이 옷 조합이 딱이네", "그 옷 조합이 딱이야", "저 옷 조합이 딱이야",
                "이 조합이 딱이네", "그 조합이 딱이야", "저 조합이 딱이야",
                "진짜 좋아", "너무 좋아", "완전 좋아", "정말 좋아",
                "이 옷 조합 괜찮아", "그 옷 조합 괜찮아", "저 옷 조합 괜찮아",
                "이 조합 괜찮아", "그 조합 괜찮아", "저 조합 괜찮아",
                "화이트, 블랙", "블랙, 화이트", "여러 색상"
            ]
            
            # 복잡한 시작 패턴 감지 및 정리
            import re
            
            # 1단계: 여러 색상+아이템이 나열된 경우 정리
            # "화이트, 블랙 화이트 버튼다운 셔츠 + 블랙 반팔에 블랙 블랙 슬림 슬랙스가"
            complex_pattern = r'^([가-힣]+),\s*([가-힣]+).*?([가-힣]+)\s+(슬랙스|팬츠|바지)가\s*잘\s*어울려'
            match = re.search(complex_pattern, response)
            if match:
                # 첫 번째 색상과 마지막 아이템만 사용
                first_color = match.group(1)
                last_item = match.group(3) + " " + match.group(4)
                
                correct_start = f"{first_color} 셔츠에 블랙 {match.group(4)}가 잘 어울려"
                response = re.sub(complex_pattern, correct_start, response)
                print(f"🔄 복잡한 패턴 정리: {correct_start}")
                
            # 2단계: 응답의 첫 문장 확인
            first_sentence = response.split('.')[0].strip()
            
            # 3단계: 금지된 시작 패턴이 있는지 확인
            for forbidden_start in forbidden_starts:
                if first_sentence.startswith(forbidden_start):
                    # JSON 데이터에서 정보 추출
                    top_color = json_data.get('top', {}).get('color', '화이트')
                    top_item = json_data.get('top', {}).get('item', '셔츠')
                    bottom_color = json_data.get('bottom', {}).get('color', '블랙')
                    bottom_item = json_data.get('bottom', {}).get('item', '슬랙스')
                    
                    # 올바른 시작으로 교체
                    correct_start = f"{top_color} {top_item}에 {bottom_color} {bottom_item}가 잘 어울려"
                    
                    # 첫 문장을 교체
                    response = response.replace(first_sentence, correct_start, 1)
                    print(f"🔄 응답 시작 부분 수정: '{forbidden_start}' → '{correct_start}'")
                    break
            
            # 4단계: 마지막으로 전체 응답이 올바른 패턴으로 시작하는지 확인
            if not re.match(r'^[가-힣]+\s+[가-힣]+에\s+[가-힣]+\s+[가-힣]+가\s+잘\s+어울려', response):
                # 강제로 올바른 시작 패턴 적용
                top_color = json_data.get('top', {}).get('color', '화이트')
                top_item = json_data.get('top', {}).get('item', '셔츠')
                bottom_color = json_data.get('bottom', {}).get('color', '블랙')
                bottom_item = json_data.get('bottom', {}).get('item', '슬랙스')
                
                # 기존 응답에서 첫 번째 문장 제거하고 올바른 시작 추가
                sentences = response.split('.')
                if len(sentences) > 1:
                    remaining_content = '.'.join(sentences[1:]).strip()
                    if remaining_content:
                        response = f"{top_color} {top_item}에 {bottom_color} {bottom_item}가 잘 어울려. {remaining_content}"
                    else:
                        response = f"{top_color} {top_item}에 {bottom_color} {bottom_item}가 잘 어울려."
                else:
                    response = f"{top_color} {top_item}에 {bottom_color} {bottom_item}가 잘 어울려."
                
                print(f"🔄 강제 패턴 적용: {response[:100]}...")
            
            print(f"✅ 응답 시작 수정 완료: {response[:150]}...")
            return response
            
        except Exception as e:
            logger.error(f"응답 시작 부분 수정 실패: {e}")
            return response

    def _improve_response_for_occasion(self, response: str, user_input: str) -> str:
        """상황별 필터링 및 용어 개선"""
        # 소개팅/데이트/비즈니스 상황 체크
        is_formal_occasion = any(keyword in user_input.lower() for keyword in ['소개팅', '데이트', '면접', '출근', '비즈니스', '회사'])
        
        # 전문 용어를 일반인이 알기 쉬운 용어로 변경
        term_replacements = {
            '드레이프': '자연스러운 주름',
            '실루엣': '옷의 형태',
            '퍼스널 컬러': '나에게 맞는 색상',
            '톤온톤': '같은 색상 계열',
            '모노톤': '한 가지 색상',
            '핏감': '핏'
        }
        
        for old_term, new_term in term_replacements.items():
            response = response.replace(old_term, new_term)
        
        # "라서" 표현을 문맥에 맞게 개선
        import random
        la_replacement_options = ['덕분에', '때문에', '이어서', '그래서']
        
        # "라서"가 포함된 문장을 찾아서 자연스럽게 변경
        if '라서' in response:
            # 문장을 분리해서 "라서" 부분을 개선
            sentences = response.split('.')
            improved_sentences = []
            
            for sentence in sentences:
                if '라서' in sentence:
                    # "라서" 앞부분과 뒷부분을 분리
                    parts = sentence.split('라서')
                    if len(parts) == 2:
                        before_la = parts[0].strip()
                        after_la = parts[1].strip()
                        replacement = random.choice(la_replacement_options)
                        improved_sentence = f"{before_la} {replacement} {after_la}"
                        improved_sentences.append(improved_sentence)
                    else:
                        improved_sentences.append(sentence)
                else:
                    improved_sentences.append(sentence)
            
            response = '. '.join(improved_sentences)
        
        # 중복 핏 정보 제거 (예: "오버핏 블랙 반팔 오버핏 티셔츠" → "오버핏 블랙 반팔 티셔츠")
        fit_terms = ['오버핏', '슬림핏', '레귤러핏', '와이드핏', '세미오버핏']
        for fit_term in fit_terms:
            # 같은 핏이 두 번 나오는 경우 첫 번째만 유지
            if f"{fit_term} " in response and f" {fit_term} " in response:
                # 첫 번째 핏 정보는 유지하고, 아이템명 앞의 중복 핏 제거
                response = response.replace(f" {fit_term} ", " ")
        
        # 소개팅/데이트/비즈니스에서 튀는 액세서리 제거
        if is_formal_occasion:
            formal_inappropriate_items = [
                '선글라스', '캡', '비니', '후드', '맨투맨', '반팔티', '티셔츠'
            ]
            for item in formal_inappropriate_items:
                if item in response:
                    # 해당 아이템이 포함된 문장을 제거하거나 대체
                    response = response.replace(f"{item}로 액센트", "깔끔한 포인트")
                    response = response.replace(f"{item} 포인트", "심플한 포인트")
                    response = response.replace(f"{item}로", "심플하게")
        
        return response

    async def get_single_expert_analysis(self, request: ExpertAnalysisRequest):
        """단일 전문가 분석"""
        expert_profile = self.expert_profiles[request.expert_type]
        
        # print(f"\n🚀 전문가 분석 시작: {request.expert_type.value}")
        # print(f"📝 사용자 입력: {request.user_input}")
        

        
        # JSON 데이터 기반 응답 시도 (새로운 방식)
        if request.json_data:
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

    async def get_single_expert_analysis_stream(self, request: ExpertAnalysisRequest):
        """단일 전문가 분석 - 스트리밍 방식"""
        expert_profile = self.expert_profiles[request.expert_type]
        
        # JSON 데이터 기반 응답 시도 (새로운 방식)
        if request.json_data:
            async for chunk in self._generate_json_based_response_stream(
                request.user_input, 
                request.expert_type,
                request.json_data
            ):
                yield chunk
            return
        
        # 참고 데이터 기반 직접 응답 시도
        reference_based_response = await self._generate_response_from_reference_data(
            request.user_input, 
            request.expert_type
        )
        
        # 참고 데이터 응답을 스트리밍으로 변환
        for i in range(0, len(reference_based_response), 10):  # 10글자씩 청크
            chunk = reference_based_response[i:i+10]
            if chunk:
                yield chunk
                await asyncio.sleep(0.05)  # 50ms 딜레이로 자연스러운 타이핑 효과
    
    async def _generate_json_based_response_stream(self, user_input: str, expert_type: FashionExpertType, json_data: dict):
        """JSON 데이터 기반 스트리밍 응답 생성"""
        try:
            expert_profile = self.expert_profiles[expert_type]
            
            # 시스템 프롬프트 구성
            system_prompt = expert_profile["prompt_template"]
            
            # 사용자 프롬프트 구성
            user_prompt = f"""사용자 입력: {user_input}

분석된 옷 조합 정보:
{json.dumps(json_data, ensure_ascii=False, indent=2)}

중요: 위 JSON 데이터의 실제 색상 조합만을 정확히 설명해주세요. 
- 상의 색상: {json_data.get('top', {}).get('color', 'N/A')}
- 하의 색상: {json_data.get('bottom', {}).get('color', 'N/A')}
- 신발 색상: {json_data.get('shoes', {}).get('color', 'N/A')}

위 정보를 바탕으로 실제 색상 조합만을 정확히 설명하는 전문가 답변을 생성해주세요."""

            # Claude API 스트리밍 호출
            async for chunk in self._call_claude_stream(system_prompt, user_prompt):
                if chunk.strip():  # 빈 청크 제외
                    yield chunk
                    
        except Exception as e:
            error_msg = f"JSON 기반 스트리밍 응답 생성 실패: {str(e)}"
            logger.error(error_msg)
            yield error_msg
    
    async def _call_claude_stream(self, system_prompt: str, user_prompt: str):
        """Claude API 스트리밍 호출"""
        try:
            # Claude API 스트리밍 호출 (anthropic 라이브러리 사용)
            stream = self.client.messages.create(
                model=settings.LLM_MODEL_NAME,
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                stream=True
            )
            
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    if chunk.delta.type == "text_delta":
                        text_chunk = chunk.delta.text
                        if text_chunk:
                            yield text_chunk
                            await asyncio.sleep(0.02)  # 20ms 딜레이로 자연스러운 타이핑 효과
                            
        except Exception as e:
            error_msg = f"Claude API 스트리밍 호출 실패: {str(e)}"
            logger.error(error_msg)
            yield error_msg

# 전역 인스턴스 생성
import os
from config import settings

# 전역 expert_service 인스턴스
expert_service = None

try:
    expert_service = SimpleFashionExpertService(api_key=settings.CLAUDE_API_KEY)
    print(f"✅ fashion_expert_service 전역 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ fashion_expert_service 전역 인스턴스 생성 실패: {e}")
    expert_service = None

def get_fashion_expert_service():
    """패션 전문가 서비스 인스턴스 반환"""
    return expert_service