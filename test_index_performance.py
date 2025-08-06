import time
import requests
import json
from datetime import datetime

class IndexPerformanceTester:
    def __init__(self, base_url="http://localhost:6020"):
        self.base_url = base_url
    
    def test_index_build(self):
        """인덱스 구축 성능 테스트"""
        print("🔍 인덱스 구축 성능 테스트 시작...")
        
        start_time = time.time()
        
        try:
            response = requests.post(f"{self.base_url}/api/admin/build-indexes")
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 인덱스 구축 성공!")
                print(f"   - 소요 시간: {duration:.2f}초")
                print(f"   - 전체 파일: {result['data']['total']}개")
                print(f"   - 인덱싱된 파일: {result['data']['indexed']}개")
                return True
            else:
                print(f"❌ 인덱스 구축 실패: {response.status_code}")
                print(f"   - 응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 인덱스 구축 중 에러: {e}")
            return False
    
    def test_index_stats(self):
        """인덱스 통계 조회 테스트"""
        print("\n🔍 인덱스 통계 조회 테스트...")
        
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/admin/index-stats")
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                stats = result['data']
                print(f"✅ 인덱스 통계 조회 성공! ({duration:.3f}초)")
                print(f"   - 전체 파일: {stats['total_files']}개")
                print(f"   - 상황별 인덱스: {stats['situation_indexes']}개")
                print(f"   - 아이템별 인덱스: {stats['item_indexes']}개")
                print(f"   - 색상별 인덱스: {stats['color_indexes']}개")
                print(f"   - 스타일링별 인덱스: {stats['styling_indexes']}개")
                return True
            else:
                print(f"❌ 인덱스 통계 조회 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 인덱스 통계 조회 중 에러: {e}")
            return False
    
    def test_search_performance(self, search_type, query, limit=10):
        """검색 성능 테스트"""
        print(f"\n🔍 {search_type} 검색 성능 테스트 (검색어: {query})...")
        
        start_time = time.time()
        
        try:
            if search_type == "situation":
                response = requests.post(f"{self.base_url}/api/admin/search-by-situation", 
                                       params={"situation": query, "limit": limit})
            elif search_type == "item":
                response = requests.post(f"{self.base_url}/api/admin/search-by-item", 
                                       params={"item": query, "limit": limit})
            else:
                print(f"❌ 지원하지 않는 검색 타입: {search_type}")
                return False
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                count = result['data']['count']
                print(f"✅ {search_type} 검색 성공! ({duration:.3f}초)")
                print(f"   - 검색 결과: {count}개")
                return True
            else:
                print(f"❌ {search_type} 검색 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ {search_type} 검색 중 에러: {e}")
            return False
    
    def test_single_api_performance(self, user_input, expert_type="style_analyst"):
        """single API 성능 테스트"""
        print(f"\n🔍 Single API 성능 테스트 (입력: {user_input})...")
        
        start_time = time.time()
        
        try:
            payload = {
                "user_input": user_input,
                "room_id": "test_room",
                "expert_type": expert_type,
                "user_profile": {},
                "context_info": {}
            }
            
            response = requests.post(f"{self.base_url}/api/expert/single", json=payload)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                search_method = result['data'].get('source', 'unknown')
                print(f"✅ Single API 성공! ({duration:.3f}초)")
                print(f"   - 검색 방식: {search_method}")
                print(f"   - 매칭된 착장: {result['data'].get('total_matches', 0)}개")
                return True
            else:
                print(f"❌ Single API 실패: {response.status_code}")
                print(f"   - 응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Single API 중 에러: {e}")
            return False
    
    def run_comprehensive_test(self):
        """종합 성능 테스트"""
        print("🚀 인덱스 성능 종합 테스트 시작")
        print("=" * 60)
        
        # 1. 인덱스 구축 테스트
        build_success = self.test_index_build()
        
        # 2. 인덱스 통계 조회 테스트
        stats_success = self.test_index_stats()
        
        # 3. 검색 성능 테스트
        search_tests = [
            ("situation", "일상"),
            ("situation", "소개팅"),
            ("item", "니트"),
            ("item", "데님"),
            ("item", "블랙")
        ]
        
        search_results = []
        for search_type, query in search_tests:
            success = self.test_search_performance(search_type, query)
            search_results.append((search_type, query, success))
        
        # 4. Single API 성능 테스트
        api_tests = [
            "일상에 입을 옷 추천해줘",
            "소개팅에 입을 옷 추천해줘",
            "니트 스웨터 코디 추천해줘",
            "블랙 데님 팬츠 코디 추천해줘"
        ]
        
        api_results = []
        for user_input in api_tests:
            success = self.test_single_api_performance(user_input)
            api_results.append((user_input, success))
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 성능 테스트 결과 요약:")
        print(f"   - 인덱스 구축: {'✅ 성공' if build_success else '❌ 실패'}")
        print(f"   - 통계 조회: {'✅ 성공' if stats_success else '❌ 실패'}")
        
        print("\n🔍 검색 성능:")
        for search_type, query, success in search_results:
            print(f"   - {search_type}:{query}: {'✅ 성공' if success else '❌ 실패'}")
        
        print("\n🎯 Single API 성능:")
        for user_input, success in api_results:
            print(f"   - {user_input[:20]}...: {'✅ 성공' if success else '❌ 실패'}")

def main():
    # 테스터 생성 및 실행
    tester = IndexPerformanceTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 