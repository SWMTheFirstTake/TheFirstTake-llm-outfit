#!/usr/bin/env python3
"""
이미지 다운로드 및 S3 업로드 스크립트
improved_mens_summer_fashion.json 파일의 이미지들을 S3에 업로드
"""

import json
import os
import requests
import boto3
from urllib.parse import urlparse
from botocore.exceptions import ClientError
import time
from tqdm import tqdm

class ImageUploader:
    def __init__(self, bucket_name="thefirsttake-combination"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')
        self.temp_dir = "temp_images"
        
        # 임시 디렉토리 생성
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def get_filename_from_url(self, image_url):
        """이미지 URL에서 파일명 추출"""
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path)
        return filename
    
    def check_json_exists_in_s3(self, filename):
        """S3의 json/ 폴더에 동일한 이름의 JSON 파일이 있는지 확인"""
        try:
            json_key = f"json/{filename.replace('.jpg', '.json').replace('.png', '.json').replace('.jpeg', '.json')}"
            self.s3_client.head_object(Bucket=self.bucket_name, Key=json_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise
    
    def download_image(self, image_url, filename):
        """이미지 다운로드"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
        except Exception as e:
            print(f"❌ 이미지 다운로드 실패 ({image_url}): {e}")
            return None
    
    def upload_to_s3(self, local_path, s3_key):
        """S3에 이미지 업로드"""
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            return True
        except Exception as e:
            print(f"❌ S3 업로드 실패 ({s3_key}): {e}")
            return False
    
    def cleanup_temp_file(self, file_path):
        """임시 파일 삭제"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ 임시 파일 삭제 실패 ({file_path}): {e}")
    
    def process_images(self, json_file_path):
        """JSON 파일의 모든 이미지 처리"""
        print(f"📖 JSON 파일 읽는 중: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 총 {len(data)}개의 이미지 항목 발견")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, item in enumerate(tqdm(data, desc="이미지 처리 중")):
            image_url = item.get('image_url')
            if not image_url:
                print(f"⚠️ 이미지 URL 없음 (항목 {i+1})")
                error_count += 1
                continue
            
            # 파일명 추출
            filename = self.get_filename_from_url(image_url)
            if not filename:
                print(f"⚠️ 파일명 추출 실패 ({image_url})")
                error_count += 1
                continue
            
            # S3 json/ 폴더에 동일한 JSON 파일이 있는지 확인
            if self.check_json_exists_in_s3(filename):
                print(f"⏭️ 이미 처리됨: {filename}")
                skip_count += 1
                continue
            
            # 이미지 다운로드
            local_path = self.download_image(image_url, filename)
            if not local_path:
                error_count += 1
                continue
            
            # S3에 업로드
            s3_key = f"image/{filename}"
            if self.upload_to_s3(local_path, s3_key):
                print(f"✅ 업로드 완료: {filename}")
                success_count += 1
            else:
                error_count += 1
            
            # 임시 파일 삭제
            self.cleanup_temp_file(local_path)
            
            # API 호출 제한 방지를 위한 짧은 대기
            time.sleep(0.1)
        
        print(f"\n📈 처리 결과:")
        print(f"✅ 성공: {success_count}개")
        print(f"⏭️ 건너뜀: {skip_count}개")
        print(f"❌ 실패: {error_count}개")
        
        # 임시 디렉토리 정리
        try:
            if os.path.exists(self.temp_dir) and not os.listdir(self.temp_dir):
                os.rmdir(self.temp_dir)
                print(f"🗑️ 임시 디렉토리 정리 완료")
        except Exception as e:
            print(f"⚠️ 임시 디렉토리 정리 실패: {e}")

def main():
    json_file = "improved_mens_summer_fashion.json"
    
    if not os.path.exists(json_file):
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        return
    
    uploader = ImageUploader()
    uploader.process_images(json_file)

if __name__ == "__main__":
    main() 