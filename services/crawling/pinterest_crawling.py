from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
from bs4 import BeautifulSoup
import json
import random
import os

class ImprovedPinterestScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        # 봇 감지 방지
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def search_pins_improved(self, query, max_pins=50):
        search_url = f"https://www.pinterest.com/search/pins/?q={query}"
        print(f"검색 시작: {search_url}")
        
        self.driver.get(search_url)
        time.sleep(5)  # 초기 로딩 대기
        
        pins_data = []
        seen_urls = set()  # 중복 방지
        scroll_attempts = 0
        max_scroll_attempts = 20
        no_new_content_count = 0
        
        while len(pins_data) < max_pins and scroll_attempts < max_scroll_attempts:
            # 현재 페이지 높이 기록
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 스크롤 다운
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 랜덤 대기 (봇 감지 방지)
            time.sleep(random.uniform(3, 5))
            
            # 추가 스크롤 (Pinterest 특성상 여러 번 스크롤 필요)
            for i in range(3):
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
            
            # 핀 요소들 찾기
            pin_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-test-id="pin"]')
            print(f"스크롤 {scroll_attempts+1}: 페이지에서 {len(pin_elements)}개 핀 발견")
            
            # 새로운 핀 수집
            new_pins_in_this_scroll = 0
            for pin in pin_elements:
                if len(pins_data) >= max_pins:
                    break
                    
                try:
                    img_element = pin.find_element(By.TAG_NAME, "img")
                    img_url = img_element.get_attribute("src")
                    
                    # 유효한 이미지 URL인지 확인
                    if img_url and img_url.startswith('https') and img_url not in seen_urls:
                        img_alt = img_element.get_attribute("alt") or "No description"
                        
                        # Pinterest 광고나 프로모션 이미지 필터링
                        if "promoted" in img_alt.lower() or "ad" in img_alt.lower():
                            continue
                            
                        try:
                            pin_link = pin.find_element(By.TAG_NAME, "a").get_attribute("href")
                        except:
                            pin_link = "No link"
                        
                        pin_data = {
                            "image_url": img_url,
                            "description": img_alt,
                            "pin_url": pin_link,
                            "query": query,
                            "collected_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        pins_data.append(pin_data)
                        seen_urls.add(img_url)
                        new_pins_in_this_scroll += 1
                        
                        print(f"수집됨 {len(pins_data)}: {img_alt[:50]}...")
                        
                except Exception as e:
                    continue
            
            # 새로운 콘텐츠가 로드되었는지 확인
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_pins_in_this_scroll == 0:
                no_new_content_count += 1
                print(f"새 핀 없음 ({no_new_content_count}번째)")
                
                if no_new_content_count >= 3:
                    print("연속으로 새 콘텐츠가 없어서 중단합니다.")
                    break
            else:
                no_new_content_count = 0  # 새 콘텐츠 발견시 리셋
                
            scroll_attempts += 1
            
            # 페이지 높이가 변하지 않으면 추가 대기
            if new_height == last_height:
                print("페이지 높이 변화 없음. 추가 대기...")
                time.sleep(3)
        
        print(f"최종 수집 완료: {len(pins_data)}개")
        return pins_data
    
    def multi_query_search(self, queries, pins_per_query=15):
        """여러 검색어로 분산 수집"""
        all_pins = []
        all_seen_urls = set()
        
        for i, query in enumerate(queries):
            print(f"\n=== 검색어 {i+1}/{len(queries)}: '{query}' ===")
            
            pins = self.search_pins_improved(query, pins_per_query)
            
            # 전체적으로 중복 제거
            unique_pins = []
            for pin in pins:
                if pin['image_url'] not in all_seen_urls:
                    unique_pins.append(pin)
                    all_seen_urls.add(pin['image_url'])
            
            all_pins.extend(unique_pins)
            print(f"'{query}'에서 {len(unique_pins)}개 고유 핀 수집 (중복 {len(pins) - len(unique_pins)}개 제거)")
            
            # 검색어 간 딜레이 (봇 감지 방지)
            if i < len(queries) - 1:
                wait_time = random.uniform(8, 12)
                print(f"{wait_time:.1f}초 대기 중...")
                time.sleep(wait_time)
        
        return all_pins
    
    def close(self):
        self.driver.quit()

# 실행 코드
if __name__ == "__main__":
    scraper = ImprovedPinterestScraper()
    
    try:
        # 다양한 검색어로 분산 수집 (남성 전용)
        search_queries = [
            # "korean men summer fashion",      # 영어 기본
            # "men summer outfit korean",       # 영어 변형
            # "korean summer street style",     # 스트릿 스타일
            # "korean casual summer men",       # 캐주얼 강조
            # "men summer fashion seoul"        # 서울 패션
            # "korean men summer style",        # 스타일 강조
            # "men summer fashion korea",       # 한국 패션
            # "korean summer men outfit",       # 아웃핏 강조
            # "korean men casual summer",       # 캐주얼 여름
            # "men summer street fashion korean", # 스트릿 패션
            # "korean men summer looks",        # 룩 강조
            # "men summer style korean fashion", # 패션 스타일
            # "korean summer men clothing",     # 의류 강조
            # "men summer outfit ideas korean", # 아웃핏 아이디어
            # "korean men summer fashion trends", # 트렌드
            # "men summer casual korean style", # 캐주얼 스타일
            # "korean summer men streetwear",   # 스트릿웨어
            # "men summer fashion inspiration korean", # 영감
            # "korean men summer wardrobe",     # 워드로브
            # "men summer style inspiration korean", # 스타일 영감
            # "korean men summer fashion male", # 남성 명시
            # "men summer outfit korean male",  # 남성 아웃핏
            # "korean men summer clothing male", # 남성 의류
            # "men summer style korean male",   # 남성 스타일
            # "korean men summer fashion guy",  # 남성 패션
            # "men summer outfit ideas korean male", # 남성 아이디어
            # "korean men summer fashion boy",  # 남성 패션
            # "men summer casual korean male",  # 남성 캐주얼
            # "korean men summer street style male", # 남성 스트릿
            # "korean men summer fashion male", # 남성 명시
            # "men summer outfit korean male",  # 남성 아웃핏
            # "korean men summer clothing male", # 남성 의류
            # "men summer style korean male",   # 남성 스타일
            # "korean men summer fashion guy",   # 남성 패션
            "korea summer street style",        # 한국 여름 스트릿
            "korea summer business casual",     # 한국 여름 비즈니스 캐주얼
            "korea summer streetwear",          # 한국 여름 스트릿웨어
            "korea summer casual style",        # 한국 여름 캐주얼
            "korea summer fashion trends"       # 한국 여름 패션 트렌드
        ]
        
        print("=== 다중 검색어로 패션 이미지 수집 시작 ===")
        all_pins = scraper.multi_query_search(search_queries, pins_per_query=30)
        
        print(f"\n🎉 총 {len(all_pins)}개의 고유한 핀을 수집했습니다!")
        
        # 결과를 JSON 파일로 저장 (기존 파일이 있으면 추가)
        output_file = "korean_mens_summer_fashion_pinterest.json"
        
        # 기존 데이터 로드 (파일이 존재하는 경우)
        existing_pins = []
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_pins = json.load(f)
                print(f"📁 기존 파일에서 {len(existing_pins)}개 데이터 로드됨")
            except Exception as e:
                print(f"⚠️ 기존 파일 읽기 실패: {e}")
                existing_pins = []
        
        # 중복 제거를 위한 기존 URL 추출
        existing_urls = set(pin['image_url'] for pin in existing_pins)
        
        # 새로운 데이터에서 중복 제거
        new_unique_pins = []
        for pin in all_pins:
            if pin['image_url'] not in existing_urls:
                new_unique_pins.append(pin)
                existing_urls.add(pin['image_url'])
        
        # 기존 + 새로운 데이터 합치기
        combined_pins = existing_pins + new_unique_pins
        
        # 파일에 저장
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(combined_pins, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(new_unique_pins)}개 새로운 데이터 추가됨 (총 {len(combined_pins)}개)")
        
        print(f"결과가 {output_file} 파일에 저장되었습니다.")
        
        # 검색어별 통계
        query_stats = {}
        for pin in all_pins:
            query = pin['query']
            query_stats[query] = query_stats.get(query, 0) + 1
        
        print("\n📊 검색어별 수집 통계:")
        for query, count in query_stats.items():
            print(f"  - {query}: {count}개")
        
        # 처음 5개 미리보기
        print("\n🖼️  수집된 이미지 미리보기 (처음 5개):")
        for i, pin in enumerate(all_pins[:5]):
            print(f"{i+1}. {pin['description'][:60]}...")
            print(f"   이미지: {pin['image_url']}")
            print(f"   출처: {pin['query']}")
            print()
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()
        print("브라우저 종료됨")