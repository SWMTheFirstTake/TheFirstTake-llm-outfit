from services.s3_service import s3_service
from services.score_calculator_service import ScoreCalculator
from services.fashion_index_service import fashion_index_service
import logging
import random

logger = logging.getLogger(__name__)

class OutfitMatcherService:
    """S3에서 매칭되는 착장을 찾는 서비스 (인덱스 기반 최적화)"""
    
    def __init__(self):
        self.score_calculator = ScoreCalculator()
        self.use_index = True  # 인덱스 사용 여부
    
    def find_matching_outfits_from_s3(self, user_input: str, expert_type: str, room_id: int = None) -> dict:
        """S3의 JSON 파일들에서 사용자 입력과 매칭되는 착장 찾기 (인덱스 기반 최적화)"""
        try:
            print(f"🔍 S3 매칭 시작: '{user_input}' (전문가: {expert_type}, room_id: {room_id})")
            
            if s3_service is None:
                print("❌ s3_service가 None입니다!")
                return None
            
            if s3_service.s3_client is None:
                print("❌ s3_service.s3_client가 None입니다!")
                return None
            
            # 인덱스 사용 여부 확인
            if self.use_index:
                print("🚀 인덱스 기반 빠른 검색 사용")
                return self._find_matching_with_index(user_input, expert_type, room_id)
            else:
                print("🐌 기존 방식 사용 (전체 스캔)")
                return self._find_matching_with_full_scan(user_input, expert_type)
            
        except Exception as e:
            print(f"❌ S3 매칭 실패: {e}")
            logger.error(f"S3 매칭 실패: {e}")
            return None
    
    def _find_matching_with_index(self, user_input: str, expert_type: str, room_id: int = None) -> dict:
        """인덱스 기반 빠른 검색"""
        try:
            # 소개팅/비즈니스 등 격식 상황인지 판별
            formal_keywords = ["소개팅", "데이트", "면접", "출근", "비즈니스", "회사", "미팅", "회의", "오피스"]
            is_formal_occasion = any(k in user_input for k in formal_keywords)
            shorts_keywords = ["반바지", "쇼츠", "하프팬츠", "숏팬츠", "숏츠", "쇼트팬츠"]

            # 사용자 입력에서 검색 조건 추출 (대화 컨텍스트 활용)
            search_criteria = self._extract_search_criteria(user_input, room_id)
            print(f"🔍 검색 조건: {search_criteria}")
            
            # 인덱스에서 후보 파일들 찾기
            candidate_files = self._find_candidates_with_index(search_criteria)
            print(f"📁 인덱스에서 {len(candidate_files)}개 후보 파일 발견")

            # 후보가 너무 적으면 S3 전체에서 보조 풀 추가로 다양성 확보
            all_files_pool = list(candidate_files)
            try:
                if len(candidate_files) < 10:
                    s3_all = s3_service.list_json_files() or []
                    # 이미 포함된 파일 제외
                    existing = {f['filename'] for f in candidate_files}
                    extras = [f for f in s3_all if f.get('filename') not in existing]
                    # 최대 30개 보조 풀 추가
                    random.shuffle(extras)
                    extras = extras[:30]
                    all_files_pool.extend(extras)
                    print(f"🎯 후보 부족으로 S3 보조 풀 추가: +{len(extras)}개 (총 {len(all_files_pool)}개)")
            except Exception as e:
                print(f"⚠️ 보조 풀 생성 중 오류: {e}")
            print(f"📁 인덱스에서 {len(candidate_files)}개 후보 파일 발견")
            
            if not candidate_files:
                print("⚠️ 인덱스에서 후보를 찾지 못해 기존 방식으로 전환")
                return self._find_matching_with_full_scan(user_input, expert_type)
            
            # 후보 파일들에 대해 점수 계산
            matching_outfits = []
            total_candidates = len(candidate_files)
            scored_candidates = 0
            
            print(f"🔍 {total_candidates}개 후보 파일에 대해 점수 계산 시작...")
            
            for i, file_info in enumerate(candidate_files):
                try:
                    # JSON 내용 가져오기
                    json_content = s3_service.get_json_content(file_info['filename'])
                    
                    # 매칭 점수 계산
                    match_score = self.score_calculator.calculate_match_score(user_input, json_content, expert_type)
                    scored_candidates += 1
                    
                    # 점수 디버그 출력 (처음 5개만)
                    if i < 5:
                        print(f"   📊 {file_info['filename']}: {match_score:.4f}")
                    
                    # 격식 상황에서는 반바지/쇼츠 계열 아웃핏을 하드 필터링
                    if is_formal_occasion:
                        extracted_items = json_content.get('extracted_items', {})
                        top_item = (extracted_items.get('top', {}) or {}).get('item', '').replace(' ', '')
                        bottom_item = (extracted_items.get('bottom', {}) or {}).get('item', '').replace(' ', '')
                        shoes_item = (extracted_items.get('shoes', {}) or {}).get('item', '').replace(' ', '')
                        
                        # 자켓/블레이저와 반바지 조합은 격식 상황에 부적절 - 엄격하게 제외
                        jacket_keywords = ["자켓", "재킷", "블레이저", "블레이져", "재킷"]
                        has_jacket = any(k in top_item for k in jacket_keywords)
                        has_shorts = any(k in bottom_item for k in shorts_keywords)
                        
                        # 부적절한 신발 체크
                        inappropriate_shoes = ["덩크", "스니커즈", "운동화", "캔버스", "컨버스"]
                        has_inappropriate_shoes = any(k in shoes_item for k in inappropriate_shoes)
                        
                        # 자켓+반바지 조합은 완전히 제외
                        if has_jacket and has_shorts:
                            print(f"🚫 격식 상황 부적절 조합(자켓+반바지) 완전 제외: {file_info['filename']}")
                            continue
                        # 반바지만 있어도 제외
                        elif has_shorts:
                            print(f"🚫 격식 상황 하의(반바지/쇼츠) 제외: {file_info['filename']}")
                            continue
                        # 부적절한 신발이 있어도 제외
                        elif has_inappropriate_shoes:
                            print(f"🚫 격식 상황 부적절 신발 제외: {file_info['filename']}")
                            continue
                    
                    # 같은 색 상하의 조합 필터링
                    extracted_items = json_content.get('extracted_items', {})
                    top_color = (extracted_items.get('top', {}) or {}).get('color', '').lower()
                    bottom_color = (extracted_items.get('bottom', {}) or {}).get('color', '').lower()
                    
                    if top_color and bottom_color and top_color == bottom_color:
                        print(f"🚫 같은 색 조합 제외: {top_color} + {bottom_color} - {file_info['filename']}")
                        continue

                    if match_score > 0.02:
                        matching_outfits.append({
                            'filename': file_info['filename'],
                            'content': json_content,
                            'score': match_score,
                            's3_url': file_info['s3_url']
                        })
                        
                except Exception as e:
                    print(f"❌ 후보 파일 분석 실패: {file_info['filename']} - {e}")
                    continue
            
            print(f"📊 점수 계산 완료: {scored_candidates}/{total_candidates}개 파일, {len(matching_outfits)}개 매칭 (점수 > 0.02)")
            
            # 점수순으로 정렬
            matching_outfits.sort(key=lambda x: x['score'], reverse=True)
            
            # 상위 15개까지 반환
            top_matches = matching_outfits[:15]
            
            print(f"✅ 인덱스 기반 매칭 완료: {len(top_matches)}개 착장 발견 (전체 매칭: {len(matching_outfits)}개)")
            if top_matches:
                print(f"   - 최고 점수: {top_matches[0]['filename']} ({top_matches[0]['score']:.3f})")
            
            return {
                'matches': top_matches,
                'all_files': all_files_pool,
                'total_files': len(candidate_files),
                'matching_count': len(matching_outfits),
                'search_method': 'index'
            }
            
        except Exception as e:
            print(f"❌ 인덱스 기반 검색 실패: {e}")
            return self._find_matching_with_full_scan(user_input, expert_type)
    
    def _find_matching_with_full_scan(self, user_input: str, expert_type: str) -> dict:
        """기존 방식: 전체 파일 스캔"""
        try:
            # S3에서 모든 JSON 파일 가져오기
            json_files = s3_service.list_json_files()
            if not json_files:
                print("❌ S3에 JSON 파일이 없습니다!")
                return None
            
            print(f"📁 S3에서 {len(json_files)}개 JSON 파일 발견")
            
            matching_outfits = []
            
            # 각 JSON 파일 분석
            for file_info in json_files:
                try:
                    # JSON 내용 가져오기
                    json_content = s3_service.get_json_content(file_info['filename'])
                    
                    # 매칭 점수 계산
                    match_score = self.score_calculator.calculate_match_score(user_input, json_content, expert_type)
                    
                    if match_score > 0.02:
                        matching_outfits.append({
                            'filename': file_info['filename'],
                            'content': json_content,
                            'score': match_score,
                            's3_url': file_info['s3_url']
                        })
                        
                except Exception as e:
                    print(f"❌ JSON 파일 분석 실패: {file_info['filename']} - {e}")
                    continue
            
            # 점수순으로 정렬
            matching_outfits.sort(key=lambda x: x['score'], reverse=True)
            
            # 상위 15개까지 반환
            top_matches = matching_outfits[:15]
            
            print(f"✅ 전체 스캔 매칭 완료: {len(top_matches)}개 착장 발견 (전체 매칭: {len(matching_outfits)}개)")
            if top_matches:
                print(f"   - 최고 점수: {top_matches[0]['filename']} ({top_matches[0]['score']:.3f})")
            
            return {
                'matches': top_matches,
                'all_files': json_files,
                'total_files': len(json_files),
                'matching_count': len(matching_outfits),
                'search_method': 'full_scan'
            }
            
        except Exception as e:
            print(f"❌ 전체 스캔 실패: {e}")
            return None
    
    def _extract_search_criteria(self, user_input: str, room_id: int = None) -> dict:
        """사용자 입력에서 검색 조건 추출 (대화 컨텍스트 활용)"""
        criteria = {
            'situations': [],
            'items': [],
            'colors': [],
            'styling': []
        }
        
        user_input_lower = user_input.lower()
        
        # 상황별 키워드
        situation_keywords = {
            "일상": ["일상", "평상시", "데일리", "일반", "보통"],
            "캐주얼": ["캐주얼", "편안", "편한", "자유"],
            "소개팅": ["소개팅", "데이트", "연애", "만남", "미팅", "첫만남"],
            "면접": ["면접", "비즈니스", "업무", "회사", "직장", "오피스"],
            "파티": ["파티", "이벤트", "축하", "기념", "특별", "클럽"],
            "여행": ["여행", "아웃도어", "야외", "레저", "휴가", "액티비티"]
        }
        
        for situation, keywords in situation_keywords.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    criteria['situations'].append(situation)
                    break
        
        # 아이템 키워드
        item_keywords = [
            "니트", "데님", "가죽", "면", "실크", "울",
            "긴팔", "반팔", "와이드", "스키니", "레귤러", "오버핏",
            "티셔츠", "셔츠", "스웨터", "후드티", "맨투맨",
            "슬랙스", "청바지", "팬츠", "반바지",
            "스니커즈", "로퍼", "옥스포드", "부츠", "샌들"
        ]
        
        for keyword in item_keywords:
            if keyword in user_input_lower:
                criteria['items'].append(keyword)
        
        # 색상 키워드
        color_keywords = [
            "블랙", "화이트", "그레이", "브라운", "네이비", "베이지",
            "검정", "흰색", "회색", "갈색", "남색", "베이지"
        ]
        
        for keyword in color_keywords:
            if keyword in user_input_lower:
                criteria['colors'].append(keyword)
        
        # 스타일링 키워드
        styling_keywords = [
            "넣기", "턱", "핏", "실루엣", "밸런스", "오버핏", "레귤러핏"
        ]
        
        for keyword in styling_keywords:
            if keyword in user_input_lower:
                criteria['styling'].append(keyword)
        
        # 🔄 대화 컨텍스트 활용: 모호한 입력이나 검색 조건이 없고 room_id가 있는 경우
        print(f"🔍 검색 조건 추출 결과: {criteria}")
        print(f"🔍 검색 조건이 비어있는가? {not any(criteria.values())}")
        
        # 모호한 입력 키워드들
        ambiguous_keywords = ["다른", "다른거", "다른거는", "또", "또다른", "추천", "추천해", "보여줘", "보여줘요"]
        is_ambiguous = any(keyword in user_input_lower for keyword in ambiguous_keywords)
        
        if room_id and (not any(criteria.values()) or is_ambiguous):
            print(f"🔄 대화 컨텍스트 활용: room_id={room_id}, 모호한 입력={is_ambiguous}")
            
            # 최근 사용된 착장들의 특성을 기반으로 검색 조건 생성
            recent_criteria = self._get_context_from_recent_outfits(room_id)
            if recent_criteria:
                print(f"📝 컨텍스트 기반 검색 조건: {recent_criteria}")
                return recent_criteria
        else:
            print(f"⚠️ 컨텍스트 기반 검색을 사용하지 않음 (조건: room_id={room_id}, 비어있음={not any(criteria.values())}, 모호한 입력={is_ambiguous})")
        
        return criteria
    
    def _get_context_from_recent_outfits(self, room_id: int) -> dict:
        """최근 사용된 착장들의 특성을 기반으로 검색 조건 생성"""
        try:
            from services.redis_service import redis_service
            
            # 최근 사용된 착장들 가져오기
            recent_outfits = redis_service.get_recent_used_outfits(room_id, limit=5)
            if not recent_outfits:
                print("⚠️ 최근 사용된 착장이 없음")
                return {}
            
            print(f"📊 최근 사용된 착장 {len(recent_outfits)}개 분석")
            
            # 각 착장의 특성 수집 (최신 순서로 처리)
            all_situations = []  # 순서를 유지하기 위해 리스트 사용
            all_items = set()
            all_colors = set()
            all_styling = set()
            
            # 가장 최근 착장의 상황을 우선적으로 사용
            primary_situations = []
            
            for i, filename in enumerate(recent_outfits):
                try:
                    # S3에서 착장 정보 가져오기
                    json_content = s3_service.get_json_content(filename)
                    if not json_content:
                        continue
                    
                    extracted_items = json_content.get('extracted_items', {})
                    situations = json_content.get('situations', [])
                    
                    # 가장 최근 착장의 상황을 우선 저장
                    if i == 0 and situations:
                        primary_situations = situations[:2]  # 최대 2개
                        print(f"🎯 최근 착장 상황: {primary_situations}")
                    
                    # 상황 추가 (최신 순서로)
                    for situation in situations:
                        if situation not in all_situations:
                            all_situations.append(situation)
                    
                    # 아이템 및 색상 추가
                    for category, item_info in extracted_items.items():
                        if isinstance(item_info, dict):
                            # 아이템명에서 키워드 추출
                            item_name = item_info.get('item', '').lower()
                            if item_name:
                                item_keywords = self._extract_keywords_from_text(item_name)
                                all_items.update(item_keywords)
                            
                            # 색상 추가
                            color = item_info.get('color', '').lower()
                            if color:
                                all_colors.add(color)
                    
                    # 스타일링 방법 추가
                    styling_methods = extracted_items.get('styling_methods', {})
                    for method_value in styling_methods.values():
                        if isinstance(method_value, str):
                            styling_keywords = self._extract_keywords_from_text(method_value.lower())
                            all_styling.update(styling_keywords)
                    
                except Exception as e:
                    print(f"❌ 착장 분석 실패: {filename} - {e}")
                    continue
            
            # 가장 최근에 사용된 특성들을 검색 조건으로 사용
            context_criteria = {
                'situations': primary_situations if primary_situations else all_situations[:2],  # 최근 착장 상황 우선
                'items': list(all_items)[:3],           # 최대 3개 아이템
                'colors': list(all_colors)[:2],         # 최대 2개 색상
                'styling': list(all_styling)[:2]        # 최대 2개 스타일링
            }
            
            print(f"✅ 컨텍스트 기반 검색 조건 생성 완료")
            return context_criteria
            
        except Exception as e:
            print(f"❌ 컨텍스트 기반 검색 조건 생성 실패: {e}")
            return {}
    
    def _extract_keywords_from_text(self, text: str) -> list:
        """텍스트에서 패션 키워드 추출"""
        keywords = []
        
        # 패션 키워드 목록
        fashion_keywords = [
            "니트", "데님", "가죽", "면", "실크", "울", "폴리에스터",
            "긴팔", "반팔", "와이드", "스키니", "레귤러", "오버핏", "슬림",
            "블랙", "화이트", "그레이", "브라운", "네이비", "베이지",
            "티셔츠", "셔츠", "니트", "스웨터", "후드티", "맨투맨",
            "슬랙스", "청바지", "팬츠", "반바지", "스커트",
            "스니커즈", "로퍼", "옥스포드", "부츠", "샌들",
            "넣기", "턱", "핏", "실루엣", "밸런스"
        ]
        
        for keyword in fashion_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def _find_candidates_with_index(self, criteria: dict) -> list:
        """인덱스를 사용하여 후보 파일들 찾기"""
        try:
            print(f"🔍 인덱스 검색 조건: {criteria}")
            
            # 고급 검색으로 후보 찾기
            candidates = fashion_index_service.advanced_search(criteria, limit=50)
            print(f"📁 인덱스 검색 결과: {len(candidates)}개 후보")
            
            # 메타데이터를 파일 정보 형태로 변환
            file_infos = []
            for candidate in candidates:
                file_infos.append({
                    'filename': candidate['filename'],
                    's3_url': candidate['s3_url']
                })
            
            print(f"✅ 인덱스 후보 변환 완료: {len(file_infos)}개")
            return file_infos
            
        except Exception as e:
            print(f"❌ 인덱스 후보 검색 실패: {e}")
            return []

# 전역 인스턴스 생성
outfit_matcher_service = OutfitMatcherService() 