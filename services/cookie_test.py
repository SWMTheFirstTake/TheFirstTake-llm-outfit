from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import json
import time
import schedule

def refresh_and_export_cookies():
    print(f"쿠키 내보내기 시작: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        driver = webdriver.Chrome()
        driver.get("https://www.youtube.com/")
        driver.refresh()
        
        # 쿠키 내보내기
        cookies = driver.get_cookies()
        filename = f"cookies_{int(time.time())}.json"
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        print(f"쿠키 저장 완료: {filename} (쿠키 개수: {len(cookies)})")
        driver.quit()
    except Exception as e:
        print(f"오류 발생: {e}")

# 즉시 한 번 실행
print("쿠키 내보내기 스크립트 시작...")
refresh_and_export_cookies()

# 1분마다 실행
schedule.every(1).minutes.do(refresh_and_export_cookies)

# 스케줄러 실행
print("스케줄러 시작 (1분마다 실행)...")
while True:
    schedule.run_pending()
    time.sleep(1)