import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.outfit_matcher_service import outfit_matcher_service

def test_search_criteria():
    """검색 조건 추출 테스트"""
    
    print("🔍 검색 조건 추출 테스트")
    print("=" * 50)
    
    test_inputs = [
        "소개팅을 가야 하는 상황이야",
        "다른거는?",
        "블랙 셔츠 추천해줘",
        "베이지 팬츠 어때?"
    ]
    
    for user_input in test_inputs:
        print(f"\n🔍 입력: '{user_input}'")
        
        # 검색 조건 추출
        criteria = outfit_matcher_service._extract_search_criteria(user_input, room_id=59)
        print(f"   - 추출된 조건: {criteria}")
        
        # 인덱스 검색 테스트
        candidates = outfit_matcher_service._find_candidates_with_index(criteria)
        print(f"   - 인덱스 후보: {len(candidates)}개")
        
        if candidates:
            print(f"   - 첫 번째 후보: {candidates[0]['filename']}")

if __name__ == "__main__":
    test_search_criteria() 