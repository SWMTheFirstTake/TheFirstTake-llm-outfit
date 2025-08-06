import requests
import json
from datetime import datetime

class PinterestAPITester:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.pinterest.com/v5"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def test_user_info(self):
        """사용자 정보 조회 테스트"""
        print("🔍 사용자 정보 조회 테스트...")
        try:
            response = requests.get(f"{self.base_url}/user_account", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                print("✅ 사용자 정보 조회 성공!")
                print(f"   - 사용자명: {user_data.get('username', 'N/A')}")
                print(f"   - 전체 이름: {user_data.get('full_name', 'N/A')}")
                print(f"   - 웹사이트: {user_data.get('website_url', 'N/A')}")
                return True
            else:
                print(f"❌ 사용자 정보 조회 실패: {response.status_code}")
                print(f"   - 응답: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 사용자 정보 조회 중 에러: {e}")
            return False
    
    def test_boards(self):
        """보드 목록 조회 테스트"""
        print("\n🔍 보드 목록 조회 테스트...")
        try:
            response = requests.get(f"{self.base_url}/boards", headers=self.headers)
            if response.status_code == 200:
                boards_data = response.json()
                boards = boards_data.get('items', [])
                print(f"✅ 보드 목록 조회 성공! (총 {len(boards)}개)")
                for i, board in enumerate(boards[:5]):  # 상위 5개만 출력
                    print(f"   {i+1}. {board.get('name', 'N/A')} - {board.get('description', 'N/A')[:50]}...")
                return True
            else:
                print(f"❌ 보드 목록 조회 실패: {response.status_code}")
                print(f"   - 응답: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 보드 목록 조회 중 에러: {e}")
            return False
    
    def test_pins(self, board_id=None):
        """핀 목록 조회 테스트"""
        print("\n🔍 핀 목록 조회 테스트...")
        try:
            if board_id:
                url = f"{self.base_url}/boards/{board_id}/pins"
            else:
                url = f"{self.base_url}/pins"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                pins_data = response.json()
                pins = pins_data.get('items', [])
                print(f"✅ 핀 목록 조회 성공! (총 {len(pins)}개)")
                for i, pin in enumerate(pins[:3]):  # 상위 3개만 출력
                    print(f"   {i+1}. {pin.get('title', 'N/A')[:50]}...")
                    print(f"      - 링크: {pin.get('link', 'N/A')}")
                return True
            else:
                print(f"❌ 핀 목록 조회 실패: {response.status_code}")
                print(f"   - 응답: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 핀 목록 조회 중 에러: {e}")
            return False
    
    def test_search_pins(self, query="fashion"):
        """핀 검색 테스트"""
        print(f"\n🔍 핀 검색 테스트 (검색어: {query})...")
        try:
            # Pinterest API v5에서는 검색 엔드포인트가 다를 수 있음
            # 여러 가능한 엔드포인트 시도
            search_endpoints = [
                f"{self.base_url}/pins/search",
                f"{self.base_url}/search/pins",
                f"{self.base_url}/search"
            ]
            
            params = {
                "query": query,
                "page_size": 5
            }
            
            for endpoint in search_endpoints:
                try:
                    print(f"   🔍 엔드포인트 시도: {endpoint}")
                    response = requests.get(endpoint, headers=self.headers, params=params)
                    if response.status_code == 200:
                        search_data = response.json()
                        pins = search_data.get('items', [])
                        print(f"✅ 핀 검색 성공! (총 {len(pins)}개)")
                        for i, pin in enumerate(pins):
                            print(f"   {i+1}. {pin.get('title', 'N/A')[:50]}...")
                            print(f"      - 이미지: {pin.get('media', {}).get('images', {}).get('1200x', {}).get('url', 'N/A')}")
                        return True
                    else:
                        print(f"   ❌ {endpoint} 실패: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ {endpoint} 에러: {e}")
                    continue
            
            print("❌ 모든 검색 엔드포인트 실패")
            return False
            
        except Exception as e:
            print(f"❌ 핀 검색 중 에러: {e}")
            return False
    
    def test_create_board(self, name="테스트 보드", description="API 테스트용 보드입니다"):
        """보드 생성 테스트"""
        print(f"\n🔍 보드 생성 테스트...")
        try:
            board_data = {
                "name": name,
                "description": description
            }
            
            response = requests.post(f"{self.base_url}/boards", headers=self.headers, json=board_data)
            if response.status_code == 201:
                board_info = response.json()
                print("✅ 보드 생성 성공!")
                print(f"   - 보드 ID: {board_info.get('id', 'N/A')}")
                print(f"   - 보드명: {board_info.get('name', 'N/A')}")
                return board_info.get('id')
            else:
                print(f"❌ 보드 생성 실패: {response.status_code}")
                print(f"   - 응답: {response.text}")
                return None
        except Exception as e:
            print(f"❌ 보드 생성 중 에러: {e}")
            return None

    def test_create_pin(self, board_id, title="테스트 핀", description="API 테스트용 핀입니다"):
        """핀 생성 테스트"""
        print(f"\n🔍 핀 생성 테스트...")
        try:
            # 간단한 테스트용 이미지 URL (실제로는 업로드된 이미지 URL 필요)
            test_image_url = "https://via.placeholder.com/600x800/FF0000/FFFFFF?text=Test+Pin"
            
            pin_data = {
                "board_id": board_id,
                "title": title,
                "description": description,
                "media_source": {
                    "source_type": "image_url",
                    "url": test_image_url
                }
            }
            
            response = requests.post(f"{self.base_url}/pins", headers=self.headers, json=pin_data)
            if response.status_code == 201:
                pin_info = response.json()
                print("✅ 핀 생성 성공!")
                print(f"   - 핀 ID: {pin_info.get('id', 'N/A')}")
                print(f"   - 제목: {pin_info.get('title', 'N/A')}")
                return True
            else:
                print(f"❌ 핀 생성 실패: {response.status_code}")
                print(f"   - 응답: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 핀 생성 중 에러: {e}")
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 Pinterest API 테스트 시작")
        print("=" * 50)
        
        # 1. 사용자 정보 테스트
        user_success = self.test_user_info()
        
        # 2. 보드 목록 테스트
        boards_success = self.test_boards()
        
        # 3. 핀 목록 테스트
        pins_success = self.test_pins()
        
        # 4. 핀 검색 테스트
        search_success = self.test_search_pins("남성 패션")
        
        # 5. 보드 생성 테스트
        board_id = self.test_create_board("패션 테스트 보드", "API 테스트용 패션 보드")
        
        # 6. 핀 생성 테스트 (보드가 생성된 경우)
        create_success = False
        if board_id:
            create_success = self.test_create_pin(board_id, "테스트 패션 핀", "API로 생성한 테스트 핀입니다")
        
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약:")
        print(f"   - 사용자 정보: {'✅ 성공' if user_success else '❌ 실패'}")
        print(f"   - 보드 목록: {'✅ 성공' if boards_success else '❌ 실패'}")
        print(f"   - 핀 목록: {'✅ 성공' if pins_success else '❌ 실패'}")
        print(f"   - 핀 검색: {'✅ 성공' if search_success else '❌ 실패'}")
        print(f"   - 보드 생성: {'✅ 성공' if board_id else '❌ 실패'}")
        print(f"   - 핀 생성: {'✅ 성공' if create_success else '❌ 실패'}")

def main():
    # Pinterest 액세스 토큰
    access_token = ""
    
    # 테스터 생성 및 실행
    tester = PinterestAPITester(access_token)
    tester.run_all_tests()

if __name__ == "__main__":
    main() 