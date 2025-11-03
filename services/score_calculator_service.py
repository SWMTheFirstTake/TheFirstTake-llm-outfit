class ScoreCalculator:
    """점수 계산을 담당하는 클래스"""

    def __init__(self):
        # 여름 시즌 부적합 아이템
        self.summer_inappropriate_items = [
            "긴팔", "롱슬리브", "긴바지", "롱팬츠",
            "코트", "패딩", "니트", "스웨터",
            "블레이저", "블레이져", "자켓", "재킷"
        ]

        # 여름 시즌 적합 아이템
        self.summer_appropriate_items = [
            "반팔", "반바지", "티셔츠", "탑"
        ]

        # 소개팅/비즈니스 부적절 아이템
        self.formal_inappropriate_items = [
            "그래픽", "오버사이즈", "맨투맨",
            "후드티", "크롭", "티셔츠", "샌들", "슬리퍼",
            # 하의(반바지/쇼츠) 계열 키워드
            "반바지", "쇼츠", "하프팬츠", "숏팬츠", "숏츠", "쇼트팬츠",
            # 부적절한 신발
            "덩크", "스니커즈", "운동화", "캔버스", "컨버스",
            # 부적절한 색상
            "오렌지", "핑크", "퍼플", "그린", "옐로우", "레드", "빨강"
        ]

        # 상황별 키워드 매핑
        self.situation_keywords = {
            "일상": ["일상", "평상시", "데일리", "일반", "보통", "스터디", "공부", "학교", "대학", "카페", "쇼핑"],
            "캐주얼": ["캐주얼", "편안", "편한", "자유", "스터디", "공부", "학교", "대학", "친구", "모임"],
            "소개팅": ["소개팅", "데이트", "연애", "만남", "미팅", "첫만남", "첫 만남"],
            "면접": ["면접", "비즈니스", "업무", "회사", "직장", "오피스", "회의"],
            "파티": ["파티", "이벤트", "축하", "기념", "특별", "클럽", "축하연"],
            "여행": ["여행", "아웃도어", "야외", "레저", "휴가", "액티비티", "운동"]
        }

    def calculate_match_score(self, user_input: str, json_content: dict, expert_type: str) -> float:
        """사용자 입력과 JSON 내용의 매칭 점수 계산"""
        score = 0.0

        try:
            user_input_lower = user_input.lower()
            extracted_items = json_content.get('extracted_items', {})
            situations = json_content.get('situations', [])

            # 0. 여성 전용 아이템 체크 (완전 제외)
            if self._has_female_only_items(extracted_items):
                print(f"❌ 여성 전용 아이템 포함으로 완전 제외")
                return -1.0  # 완전히 제외하기 위한 최저 점수

            # 1. 시즌 적합성 점수
            score += self._calculate_season_score(extracted_items)

            # 2. 색상 조합 점수
            score += self._calculate_color_score(extracted_items)

            # 3. 상황 적합성 점수
            score += self._calculate_situation_score(user_input_lower, situations)

            # 4. 아이템 매칭 점수
            score += self._calculate_item_match_score(user_input_lower, extracted_items)

            # 5. 스타일링 방법 점수
            score += self._calculate_styling_score(user_input_lower, extracted_items, expert_type)

            # 6. 다양성 보너스
            score += self._calculate_diversity_bonus(situations, extracted_items)

            # 7. 상황별 부적절 아이템 감점 (새로 추가)
            score += self._calculate_situation_inappropriate_penalty(user_input_lower, extracted_items)

            return min(score, 1.0)  # 최대 1.0으로 제한

        except Exception as e:
            print(f"❌ 매칭 점수 계산 실패: {e}")
            return 0.0

    def _calculate_season_score(self, extracted_items: dict) -> float:
        """시즌 적합성 점수 계산"""
        score = 0.0

        top_item = extracted_items.get("top", {}).get("item", "").lower()
        bottom_item = extracted_items.get("bottom", {}).get("item", "").lower()

        # 여름에 부적합한 아이템 체크 (감점 증가)
        if any(item in top_item for item in self.summer_inappropriate_items) or \
           any(item in bottom_item for item in self.summer_inappropriate_items):
            score -= 0.6  # -0.3에서 -0.6으로 증가

        # 여름에 적합한 아이템 체크
        if any(item in top_item for item in self.summer_appropriate_items) or \
           any(item in bottom_item for item in self.summer_appropriate_items):
            score += 0.2

        return score

    def _calculate_color_score(self, extracted_items: dict) -> float:
        """색상 조합 점수 계산"""
        score = 0.0

        top_color = extracted_items.get("top", {}).get("color", "").lower()
        bottom_color = extracted_items.get("bottom", {}).get("color", "").lower()

        # 같은 색 상하의 조합 감점 (모든 색상에 적용)
        if top_color and bottom_color and top_color == bottom_color:
            score -= 0.8  # 큰 감점
            print(f"⚠️ 같은 색 조합 감점: {top_color} + {bottom_color} (-0.8점)")

        return score

    def _calculate_situation_score(self, user_input: str, situations: list) -> float:
        """상황 적합성 점수 계산"""
        score = 0.0

        # 상황 태그 직접 매칭
        for situation in situations:
            if situation.lower() in user_input:
                score += 0.4
                return score

        # 상황 유사성 점수
        score += self._calculate_situation_similarity(user_input, situations)

        return score

    def _calculate_item_match_score(self, user_input: str, extracted_items: dict) -> float:
        """아이템 매칭 점수 계산"""
        score = 0.0

        for category, item_info in extracted_items.items():
            if isinstance(item_info, dict):
                item_name = item_info.get('item', '').lower()
                item_color = item_info.get('color', '').lower()
                item_fit = item_info.get('fit', '').lower()

                # 색상+아이템 조합 매칭 (예: "블랙 셔츠", "셔츠 블랙")
                if item_name and item_color:
                    combined_keyword1 = f"{item_color} {item_name}"
                    combined_keyword2 = f"{item_name} {item_color}"
                    if combined_keyword1 in user_input or combined_keyword2 in user_input:
                        score += 0.8  # 높은 점수로 정확한 매칭 보상
                        print(f"✅ 색상+아이템 정확 매칭: {combined_keyword1 or combined_keyword2} (+0.8점)")
                        continue  # 정확 매칭 시 개별 점수는 추가하지 않음
                
                if item_name and item_name in user_input:
                    score += 0.3
                if item_color and item_color in user_input:
                    score += 0.2
                if item_fit and item_fit in user_input:
                    score += 0.2

        return score

    def _calculate_styling_score(self, user_input: str, extracted_items: dict, expert_type: str) -> float:
        """스타일링 방법 점수 계산"""
        score = 0.0

        styling_methods = extracted_items.get('styling_methods', {})
        if isinstance(styling_methods, dict):
            for method_key, method_value in styling_methods.items():
                if isinstance(method_value, str) and method_value.lower() in user_input:
                    if method_key in ['top_wearing_method', 'tuck_degree', 'fit_details', 'silhouette_balance']:
                        score += 0.3
                    else:
                        score += 0.2

        # 전문가 타입별 가중치
        if expert_type == "stylist" and styling_methods:
            score += 0.1

        return score

    def _calculate_diversity_bonus(self, situations: list, extracted_items: dict) -> float:
        """다양성 보너스 점수 계산"""
        bonus = 0.0

        # 상황 다양성 보너스
        if len(situations) >= 3:
            bonus += 0.05
        elif len(situations) >= 2:
            bonus += 0.03

        # 아이템 다양성 보너스
        item_categories = ['top', 'bottom', 'shoes', 'accessories']
        filled_categories = sum(1 for category in item_categories
                              if category in extracted_items and
                              extracted_items[category] and
                              isinstance(extracted_items[category], dict) and
                              extracted_items[category].get('item'))

        if filled_categories >= 4:
            bonus += 0.05
        elif filled_categories >= 3:
            bonus += 0.03

        # 스타일링 방법 다양성 보너스
        styling_methods = extracted_items.get('styling_methods', {})
        if isinstance(styling_methods, dict):
            filled_styling_methods = sum(1 for key, value in styling_methods.items()
                                        if isinstance(value, str) and value.strip())

            if filled_styling_methods >= 5:
                bonus += 0.03
            elif filled_styling_methods >= 3:
                bonus += 0.02

        return bonus

    def _calculate_situation_similarity(self, user_input: str, situations: list) -> float:
        """사용자 입력과 상황 태그의 유사성 점수 계산"""
        score = 0.0

        for situation, keywords in self.situation_keywords.items():
            for keyword in keywords:
                if keyword in user_input and situation in situations:
                    score += 0.6
                    break

        if situations:
            score += 0.1

        return min(score, 0.8)

    def apply_expert_filter(self, candidates: list, expert_type: str) -> list:
        """전문가 타입별 필터링 적용"""
        if not candidates:
            return candidates

    def _calculate_situation_inappropriate_penalty(self, user_input: str, extracted_items: dict) -> float:
        """상황별 부적절 아이템 감점 계산"""
        penalty = 0.0
        
        # 소개팅/비즈니스 상황 체크
        formal_keywords = ["소개팅", "데이트", "면접", "출근", "비즈니스", "회사", "미팅", "회의", "오피스"]
        is_formal_occasion = any(keyword in user_input for keyword in formal_keywords)
        
        if is_formal_occasion:
            top_item = extracted_items.get("top", {}).get("item", "").lower()
            bottom_item = extracted_items.get("bottom", {}).get("item", "").lower()
            
            # 소개팅/비즈니스에 부적절한 아이템들
            formal_inappropriate_items = [
                "그래픽", "오버사이즈", "맨투맨", "후드티", "크롭", 
                "티셔츠", "후드", "스웨트", "트레이닝", "운동복",
                # 하의(반바지/쇼츠) 계열 키워드(동의어 포함)
                "반바지", "쇼츠", "하프팬츠", "숏팬츠", "숏츠", "쇼트팬츠"
            ]
            
            # 자켓/블레이저와 반바지 조합은 격식 상황에 부적절
            jacket_keywords = ["자켓", "재킷", "블레이저", "블레이져", "재킷"]
            shorts_keywords = ["반바지", "쇼츠", "하프팬츠", "숏팬츠", "숏츠", "쇼트팬츠"]
            
            top_item_no_space = top_item.replace(" ", "")
            bottom_item_no_space = bottom_item.replace(" ", "")
            
            has_jacket = any(k in top_item_no_space for k in jacket_keywords)
            has_shorts = any(k in bottom_item_no_space for k in shorts_keywords)
            
            # 자켓+반바지 조합은 격식 상황에 매우 부적절 - 완전 제외
            if has_jacket and has_shorts:
                penalty -= 10.0  # 완전 제외를 위한 최대 감점
                print(f"🚫 소개팅/비즈니스에 부적절한 조합(자켓+반바지) 완전 제외 (-10.0점)")
            else:
                # 상의에서 부적절한 아이템 체크
                for item in formal_inappropriate_items:
                    if item in top_item_no_space:
                        penalty -= 0.8  # 큰 감점
                        print(f"⚠️ 소개팅/비즈니스에 부적절한 상의 발견: {item} (-0.8점)")
                        break
                
                # 하의에서 부적절한 아이템 체크
                for item in formal_inappropriate_items:
                    if item in bottom_item_no_space:
                        penalty -= 0.6  # 중간 감점
                        print(f"⚠️ 소개팅/비즈니스에 부적절한 하의 발견: {item} (-0.6점)")
                        break
        
        return penalty

    def _has_female_only_items(self, extracted_items: dict) -> bool:
        """여성 전용 아이템이 포함되어 있는지 체크"""
        # 여성 전용 아이템 목록
        female_only_items = [
            "스커트", "드레스", "블라우스", "미디", "미니", "맥시", "원피스",
            "플리츠", "주름", "리본", "레이스", "프릴", "볼륨", "플레어",
            "A라인", "H라인", "X라인", "Y라인", "I라인", "O라인",
            "펌프스", "힐", "웨지", "플랫폼", "스틸레토", "메리제인",
            "크롭", "캐미솔", "탑", "튜브탑", "할리톱", "오프숄더",
            "원숄더", "스트랩리스", "백리스", "키홀", "컷아웃", "하프팬츠", "스키니", "숏팬츠"
        ]
        
        # 모든 아이템 카테고리에서 여성 전용 아이템 체크
        for category, item_info in extracted_items.items():
            if isinstance(item_info, dict):
                item_name = item_info.get('item', '').lower()
                item_style = item_info.get('style', '').lower()
                item_fit = item_info.get('fit', '').lower()
                
                # 아이템명, 스타일, 핏에서 여성 전용 키워드 체크 (공백 제거)
                all_item_text = f"{item_name} {item_style} {item_fit}".lower().replace(" ", "")
                
                for female_item in female_only_items:
                    if female_item in all_item_text:
                        print(f"🚫 여성 전용 아이템 발견: {female_item} in {category}")
                        return True
        
        return False

        if expert_type == "style_analyst":
            # 스타일 분석가: 다양한 스타일링 방법이 있는 것 우선
            filtered_candidates = []
            for match in candidates:
                styling_methods = match['content'].get('extracted_items', {}).get('styling_methods', {})
                if isinstance(styling_methods, dict) and len(styling_methods) >= 2:
                    filtered_candidates.append(match)

            if filtered_candidates:
                print(f"🎯 스타일 분석가 필터 적용: {len(filtered_candidates)}개 후보")
                return filtered_candidates
            else:
                print(f"⚠️ 스타일 분석가 필터 적용 불가, 전체 후보 사용")

        elif expert_type == "trend_expert":
            # 트렌드 전문가: 최신 스타일 (최근 파일) 우선
            recent_candidates = sorted(candidates, key=lambda x: x['filename'], reverse=True)[:5]
            if recent_candidates:
                print(f"🎯 트렌드 전문가 필터 적용: 최근 5개 파일")
                return recent_candidates
            else:
                print(f"⚠️ 트렌드 전문가 필터 적용 불가, 전체 후보 사용")

        elif expert_type == "color_expert":
            # 컬러 전문가: 다양한 색상이 있는 것 우선
            filtered_candidates = []
            for match in candidates:
                items = match['content'].get('extracted_items', {})
                colors = set()
                for category, item_info in items.items():
                    if isinstance(item_info, dict) and item_info.get('color'):
                        colors.add(item_info['color'])
                if len(colors) >= 2:
                    filtered_candidates.append(match)

            if filtered_candidates:
                print(f"🎯 컬러 전문가 필터 적용: {len(filtered_candidates)}개 후보")
                return filtered_candidates
            else:
                print(f"⚠️ 컬러 전문가 필터 적용 불가, 전체 후보 사용")

        elif expert_type == "fitting_coordinator":
            # 핏팅 코디네이터: 다양한 핏 정보가 있는 것 우선
            filtered_candidates = []
            for match in candidates:
                items = match['content'].get('extracted_items', {})
                fits = set()
                for category, item_info in items.items():
                    if isinstance(item_info, dict) and item_info.get('fit'):
                        fits.add(item_info['fit'])
                if len(fits) >= 2:
                    filtered_candidates.append(match)

            if filtered_candidates:
                print(f"🎯 핏팅 코디네이터 필터 적용: {len(filtered_candidates)}개 후보")
                return filtered_candidates
            else:
                print(f"⚠️ 핏팅 코디네이터 필터 적용 불가, 전체 후보 사용")

        return candidates 