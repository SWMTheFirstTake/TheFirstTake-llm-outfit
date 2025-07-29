import asyncio
import requests
import os
from datetime import datetime

async def test_s3_upload():
    """S3 업로드 API 테스트"""
    
    print("🔍 S3 업로드 API 테스트 시작")
    
    # API 서버 URL (실제 서버 URL로 변경 필요)
    base_url = "http://localhost:6020"
    
    try:
        # 1. 서비스 상태 확인
        print("\n1️⃣ 서비스 상태 확인...")
        status_response = requests.get(f"{base_url}/api/vision/status")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print("✅ 서비스 상태 조회 성공")
            print(f"   Claude Vision: {status_data['data']['claude_vision_service']['status']}")
            print(f"   S3 Service: {status_data['data']['s3_service']['status']}")
            print(f"   S3 Bucket: {status_data['data']['s3_service']['bucket_name']}")
            print(f"   S3 Prefix: {status_data['data']['s3_service']['bucket_prefix']}")
        else:
            print(f"❌ 서비스 상태 조회 실패: {status_response.status_code}")
            return
        
        # 2. 테스트용 이미지 파일 생성 (실제 테스트시에는 실제 이미지 파일 사용)
        print("\n2️⃣ 테스트용 이미지 파일 생성...")
        test_image_path = "test_image.jpg"
        
        # 간단한 테스트 이미지 생성 (실제로는 실제 이미지 파일을 사용하세요)
        if not os.path.exists(test_image_path):
            # 1x1 픽셀 JPEG 이미지 생성
            test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
            
            with open(test_image_path, 'wb') as f:
                f.write(test_image_data)
            print(f"✅ 테스트 이미지 생성: {test_image_path}")
        else:
            print(f"✅ 기존 테스트 이미지 사용: {test_image_path}")
        
        # 3. S3 업로드 테스트
        print("\n3️⃣ S3 업로드 테스트...")
        
        with open(test_image_path, 'rb') as f:
            files = {'file': (test_image_path, f, 'image/jpeg')}
            upload_response = requests.post(f"{base_url}/api/vision/upload-image", files=files)
        
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            print("✅ S3 업로드 성공!")
            print(f"   S3 URL: {upload_data['data']['s3_url']}")
            print(f"   파일명: {upload_data['data']['filename']}")
            print(f"   파일 크기: {upload_data['data']['file_size']} bytes")
            
            # 4. 업로드된 이미지로 분석 테스트
            print("\n4️⃣ 업로드된 이미지로 분석 테스트...")
            
            # S3 URL을 사용한 분석 요청
            analysis_request = {
                "image_url": upload_data['data']['s3_url'],
                "prompt": None
            }
            
            analysis_response = requests.post(
                f"{base_url}/api/vision/analyze-outfit",
                json=analysis_request
            )
            
            if analysis_response.status_code == 200:
                analysis_data = analysis_response.json()
                print("✅ 이미지 분석 성공!")
                print(f"   분석 결과: {analysis_data['data']['extracted_items']['top']['item']}")
                print(f"   색상: {analysis_data['data']['extracted_items']['top']['color']}")
                print(f"   핏: {analysis_data['data']['extracted_items']['top']['fit']}")
            else:
                print(f"❌ 이미지 분석 실패: {analysis_response.status_code}")
                print(f"   에러: {analysis_response.text}")
        else:
            print(f"❌ S3 업로드 실패: {upload_response.status_code}")
            print(f"   에러: {upload_response.text}")
        
        # 5. 정리
        print("\n5️⃣ 정리...")
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f"✅ 테스트 이미지 삭제: {test_image_path}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_s3_upload()) 