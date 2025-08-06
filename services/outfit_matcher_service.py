from services.s3_service import s3_service
from services.score_calculator_service import ScoreCalculator
from services.fashion_index_service import fashion_index_service
import logging

logger = logging.getLogger(__name__)

class OutfitMatcherService:
    """S3에서 매칭되는 착장을 찾는 서비스 (인덱스 기반 최적화)"""
    
    def __init__(self):
        self.score_calculator = ScoreCalculator()
        self.use_index = True  # 인덱스 사용 여부
    
    def find_matching_outfits_from_s3(self, user_input: str, expert_type: str) -> dict:
        """S3의 JSON 파일들에서 사용자 입력과 매칭되는 착장 찾기 (인덱스 기반 최적화)"""
        try:
            print(f"🔍 S3 매칭 시작: '{user_input}' (전문가: {expert_type})")
            
            if s3_service is None:
                print("❌ s3_service가 None입니다!")
                return None
            
            if s3_service.s3_client is None:
                print("❌ s3_service.s3_client가 None입니다!")
                return None
            
            # 인덱스 사용 여부 확인
            if self.use_index:
                print("🚀 인덱스 기반 빠른 검색 사용")
                return self._find_matching_with_index(user_input, expert_type)
            else:
                print("🐌 기존 방식 사용 (전체 스캔)")
                return self._find_matching_with_full_scan(user_input, expert_type)
            
        except Exception as e:
            print(f"❌ S3 매칭 실패: {e}")
            logger.error(f"S3 매칭 실패: {e}")
            return None
    
    def _find_matching_with_index(self, user_input: str, expert_type: str) -> dict:
        """인덱스 기반 빠른 검색"""
        try:
            # 사용자 입력에서 검색 조건 추출
            search_criteria = self._extract_search_criteria(user_input)
            print(f"🔍 검색 조건: {search_criteria}")
            
            # 인덱스에서 후보 파일들 찾기
            candidate_files = self._find_candidates_with_index(search_criteria)
            print(f"📁 인덱스에서 {len(candidate_files)}개 후보 파일 발견")
            
            if not candidate_files:
                print("⚠️ 인덱스에서 후보를 찾지 못해 기존 방식으로 전환")
                return self._find_matching_with_full_scan(user_input, expert_type)
            
            # 후보 파일들에 대해 점수 계산
            matching_outfits = []
            for file_info in candidate_files:
                try:
                    # JSON 내용 가져오기
                    json_content = s3_service.get_json_content(file_info['filename'])
                    
                    # 매칭 점수 계산
                    match_score = self.score_calculator.calculate_match_score(user_input, json_content, expert_type)
                    
                    if match_score > 0.05:
                        matching_outfits.append({
                            'filename': file_info['filename'],
                            'content': json_content,
                            'score': match_score,
                            's3_url': file_info['s3_url']
                        })
                        
                except Exception as e:
                    print(f"❌ 후보 파일 분석 실패: {file_info['filename']} - {e}")
                    continue
            
            # 점수순으로 정렬
            matching_outfits.sort(key=lambda x: x['score'], reverse=True)
            
            # 상위 15개까지 반환
            top_matches = matching_outfits[:15]
            
            print(f"✅ 인덱스 기반 매칭 완료: {len(top_matches)}개 착장 발견 (전체 매칭: {len(matching_outfits)}개)")
            if top_matches:
                print(f"   - 최고 점수: {top_matches[0]['filename']} ({top_matches[0]['score']:.3f})")
            
            return {
                'matches': top_matches,
                'all_files': candidate_files,
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
                    
                    if match_score > 0.05:
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
    
    def _extract_search_criteria(self, user_input: str) -> dict:
        """사용자 입력에서 검색 조건 추출"""
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
        
        return criteria
    
    def _find_candidates_with_index(self, criteria: dict) -> list:
        """인덱스를 사용하여 후보 파일들 찾기"""
        try:
            # 고급 검색으로 후보 찾기
            candidates = fashion_index_service.advanced_search(criteria, limit=50)
            
            # 메타데이터를 파일 정보 형태로 변환
            file_infos = []
            for candidate in candidates:
                file_infos.append({
                    'filename': candidate['filename'],
                    's3_url': candidate['s3_url']
                })
            
            return file_infos
            
        except Exception as e:
            print(f"❌ 인덱스 후보 검색 실패: {e}")
            return []

# 전역 인스턴스 생성
outfit_matcher_service = OutfitMatcherService() 