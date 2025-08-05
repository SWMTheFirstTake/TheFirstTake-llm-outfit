from services.s3_service import s3_service
from services.score_calculator_service import ScoreCalculator
import logging

logger = logging.getLogger(__name__)

class OutfitMatcherService:
    """S3에서 매칭되는 착장을 찾는 서비스"""
    
    def __init__(self):
        self.score_calculator = ScoreCalculator()
    
    def find_matching_outfits_from_s3(self, user_input: str, expert_type: str) -> dict:
        """S3의 JSON 파일들에서 사용자 입력과 매칭되는 착장 찾기"""
        try:
            print(f"🔍 S3 매칭 시작: '{user_input}' (전문가: {expert_type})")
            
            if s3_service is None:
                print("❌ s3_service가 None입니다!")
                return None
            
            if s3_service.s3_client is None:
                print("❌ s3_service.s3_client가 None입니다!")
                return None
            
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
                    
                    if match_score > 0.05:  # 임계값을 더 낮춰서 더 많은 착장 포함
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
            
            # 상위 15개까지 반환 (더 많은 선택지)
            top_matches = matching_outfits[:15]
            
            print(f"✅ S3 매칭 완료: {len(top_matches)}개 착장 발견 (전체 매칭: {len(matching_outfits)}개)")
            if top_matches:
                print(f"   - 최고 점수: {top_matches[0]['filename']} ({top_matches[0]['score']:.3f})")
            
            return {
                'matches': top_matches,
                'all_files': json_files,  # 모든 파일 정보 추가
                'total_files': len(json_files),
                'matching_count': len(matching_outfits)
            }
            
        except Exception as e:
            print(f"❌ S3 매칭 실패: {e}")
            logger.error(f"S3 매칭 실패: {e}")
            return None

# 전역 인스턴스 생성
outfit_matcher_service = OutfitMatcherService() 