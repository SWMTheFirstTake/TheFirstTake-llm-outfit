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
        max_scroll_attempts = 30  # 더 많은 스크롤 시도
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
                        
                        # 여성 관련 키워드 필터링 (남성 패션만 수집)
                        female_keywords = [
                            "woman", "women", "girl", "girls", "female", "lady", "ladies",
                            "여성", "여자", "걸", "레이디", "우먼", "걸스", "여성용",
                            "dress", "skirt", "heels", "makeup", "nail", "purse", "handbag",
                            "원피스", "치마", "힐", "메이크업", "네일", "핸드백", "가방"
                        ]
                        
                        # 설명에 여성 관련 키워드가 있으면 건너뛰기
                        if any(keyword in img_alt.lower() for keyword in female_keywords):
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
                
                if no_new_content_count >= 5:  # 더 많은 시도 후 중단
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
        # 한국 남성 패션 전용 검색어 (1000장 수집 목표)
        search_queries = [
            # 기본 남성 패션 검색어
            "korean men fashion",
            "korean male style",
            "korean guy outfit",
            "korean men streetwear",
            "korean men casual",
            "korean men business casual",
            
            # 계절별 남성 패션
            "korean men summer fashion",
            "korean men winter style",
            "korean men spring outfit",
            "korean men fall fashion",
            
            # 스타일별 남성 패션
            "korean men street style",
            "korean men formal wear",
            "korean men casual wear",
            "korean men smart casual",
            "korean men minimalist fashion",
            "korean men trendy style",
            
            # 연령대별 남성 패션
            "korean young men fashion",
            "korean men in 20s style",
            "korean men in 30s outfit",
            "korean college men fashion",
            
            # 특정 아이템 중심
            "korean men shirt style",
            "korean men jacket fashion",
            "korean men pants outfit",
            "korean men accessories",
            
            # K-pop/연예인 스타일
            "korean idol men fashion",
            "kpop men style",
            "korean actor fashion",
            "korean celebrity men outfit",
            
            # 지역/문화 특화
            "seoul men fashion",
            "korean office men style",
            "korean university men fashion",
            "korean men daily outfit",
            
            # 영어 변형
            "men fashion korea",
            "male style korean",
            "guy outfit korea",
            "korean masculine style",
            "korean men clothing",
            "korean men wardrobe",
            
            # 상황별/데이트룩 등
            "korean men date outfit",
            "korean men date fashion",
            "korean guy date look",
            "korean men romantic style",
            "korean men dinner date outfit",
            "korean men casual date look",
            "korean men weekend outfit",
            "korean men party style",
            "korean men night out fashion",
            "korean men cafe outfit",
            "korean men movie date style"
        ]
        
        print("=== 1000장 한국 남성 패션 이미지 수집 시작 ===")
        # 1000장 목표를 위해 검색어당 더 많은 이미지 수집
        target_total = 1000
        pins_per_query = max(30, target_total // len(search_queries) + 10)
        print(f"검색어 {len(search_queries)}개, 검색어당 {pins_per_query}개 목표")
        
        all_pins = scraper.multi_query_search(search_queries, pins_per_query=pins_per_query)
        
        print(f"\n🎉 총 {len(all_pins)}개의 고유한 핀을 수집했습니다!")
        
        # 목표 달성 여부 확인
        if len(all_pins) >= target_total:
            print(f"✅ 목표 {target_total}장 달성! ({len(all_pins)}장 수집)")
        else:
            print(f"⚠️ 목표 {target_total}장 중 {len(all_pins)}장 수집 ({len(all_pins)/target_total*100:.1f}%)")
            print("💡 더 많은 이미지를 원한다면 다시 실행하거나 검색어를 추가해보세요.")
        
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