import boto3
import logging
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        """S3 서비스 초기화"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.S3_COMBINATION_BUCKET_NAME
            self.bucket_prefix = settings.S3_COMBINATION_BUCKET_IMAGE_PREFIX
            self.bucket_json_prefix = settings.S3_COMBINATION_BUCKET_JSON_PREFIX
            
            print(f"✅ S3 서비스 초기화 성공")
            print(f"   - 버킷: {self.bucket_name}")
            print(f"   - 프리픽스: {self.bucket_prefix}")
            print(f"   - 리전: {settings.AWS_REGION}")
            
        except Exception as e:
            print(f"❌ S3 서비스 초기화 실패: {e}")
            self.s3_client = None
    
    def upload_image(self, image_bytes: bytes, original_filename: str = None) -> str:
        """이미지를 S3에 업로드"""
        try:
            if not self.s3_client:
                raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
            
            # 파일 확장자 추출 및 ContentType 매핑
            if original_filename:
                file_extension = original_filename.split('.')[-1].lower()
                if file_extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    file_extension = 'jpg'  # 기본값
            else:
                file_extension = 'jpg'
            
            # ContentType 매핑
            content_type_mapping = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp',
                'gif': 'image/gif'
            }
            content_type = content_type_mapping.get(file_extension, 'image/jpeg')
            
            # 타임스탬프 기반 파일명 생성 (마이크로초 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 마이크로초 3자리만 사용
            s3_key = f"{self.bucket_prefix}/{timestamp}.{file_extension}"
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_bytes,
                ContentType=content_type
            )
            
            # S3 URL 생성
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            
            print(f"✅ S3 업로드 성공: {s3_url}")
            return s3_url
            
        except Exception as e:
            print(f"❌ S3 업로드 실패: {e}")
            logger.error(f"S3 업로드 실패: {e}")
            raise Exception(f"S3 업로드 실패: {str(e)}")
    
    def upload_json(self, json_data: dict, filename: str) -> str:
        """JSON 데이터를 S3에 업로드"""
        try:
            if not self.s3_client:
                raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
            
            import json as json_module
            
            # JSON 문자열로 변환
            json_string = json_module.dumps(json_data, ensure_ascii=False, indent=2)
            json_bytes = json_string.encode('utf-8')
            
            # S3 키 생성
            s3_key = f"{self.bucket_json_prefix}/{filename}.json"
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_bytes,
                ContentType='application/json'
            )
            
            # S3 URL 생성
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            
            print(f"✅ JSON S3 업로드 성공: {s3_url}")
            return s3_url
            
        except Exception as e:
            print(f"❌ JSON S3 업로드 실패: {e}")
            logger.error(f"JSON S3 업로드 실패: {e}")
            raise Exception(f"JSON S3 업로드 실패: {str(e)}")
    
    def check_json_exists(self, filename: str) -> bool:
        """JSON 파일이 S3에 존재하는지 확인"""
        try:
            if not self.s3_client:
                return False
            
            s3_key = f"{self.bucket_json_prefix}/{filename}.json"
            
            # S3에서 객체 존재 여부 확인
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
            
        except Exception as e:
            # 파일이 존재하지 않는 경우
            return False
    
    def list_image_files(self) -> list:
        """S3의 /image 디렉토리에서 모든 이미지 파일 목록을 가져옴"""
        try:
            if not self.s3_client:
                return []
            
            # S3에서 /image 디렉토리의 모든 객체 조회
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.bucket_prefix + "/"
            )
            
            image_files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # /image/ 디렉토리의 파일만 필터링
                    if key.startswith(self.bucket_prefix + "/") and key != self.bucket_prefix + "/":
                        # 파일명 추출 (확장자 제거)
                        filename = key.split('/')[-1].split('.')[0]
                        s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
                        
                        image_files.append({
                            "s3_key": key,
                            "filename": filename,
                            "s3_url": s3_url,
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat()
                        })
            
            print(f"✅ S3 이미지 파일 목록 조회 완료: {len(image_files)}개 파일")
            return image_files
            
        except Exception as e:
            print(f"❌ S3 이미지 파일 목록 조회 실패: {e}")
            logger.error(f"S3 이미지 파일 목록 조회 실패: {e}")
            return []
    
    def get_files_without_json(self) -> list:
        """JSON 파일이 없는 이미지 파일들만 반환"""
        try:
            image_files = self.list_image_files()
            files_without_json = []
            
            for image_file in image_files:
                filename = image_file['filename']
                if not self.check_json_exists(filename):
                    files_without_json.append(image_file)
            
            print(f"✅ JSON이 없는 이미지 파일 조회 완료: {len(files_without_json)}개 파일")
            return files_without_json
            
        except Exception as e:
            print(f"❌ JSON이 없는 이미지 파일 조회 실패: {e}")
            logger.error(f"JSON이 없는 이미지 파일 조회 실패: {e}")
            return []
    
    def list_json_files(self) -> list:
        """S3의 /json 디렉토리에서 모든 JSON 파일 목록을 가져옴"""
        try:
            if not self.s3_client:
                return []
            
            # S3에서 /json 디렉토리의 모든 객체 조회
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.bucket_json_prefix + "/"
            )
            
            json_files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # /json/ 디렉토리의 파일만 필터링
                    if key.startswith(self.bucket_json_prefix + "/") and key != self.bucket_json_prefix + "/":
                        # 파일명 추출 (.json 확장자 제거)
                        filename = key.split('/')[-1].replace('.json', '')
                        s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
                        
                        json_files.append({
                            "s3_key": key,
                            "filename": filename,
                            "s3_url": s3_url,
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat()
                        })
            
            print(f"✅ S3 JSON 파일 목록 조회 완료: {len(json_files)}개 파일")
            return json_files
            
        except Exception as e:
            print(f"❌ S3 JSON 파일 목록 조회 실패: {e}")
            logger.error(f"S3 JSON 파일 목록 조회 실패: {e}")
            return []
    
    def get_json_content(self, filename: str) -> dict:
        """특정 JSON 파일의 내용을 가져옴"""
        try:
            if not self.s3_client:
                raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
            
            s3_key = f"{self.bucket_json_prefix}/{filename}.json"
            
            # S3에서 JSON 파일 다운로드
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # JSON 내용 파싱
            import json as json_module
            json_content = json_module.loads(response['Body'].read().decode('utf-8'))
            
            print(f"✅ JSON 파일 내용 조회 완료: {filename}")
            return json_content
            
        except Exception as e:
            print(f"❌ JSON 파일 내용 조회 실패: {filename} - {e}")
            logger.error(f"JSON 파일 내용 조회 실패: {filename} - {e}")
            raise Exception(f"JSON 파일 내용 조회 실패: {str(e)}")
    
    def update_json_situations(self, filename: str, situations: list) -> str:
        """JSON 파일의 situations 필드를 업데이트"""
        try:
            if not self.s3_client:
                raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
            
            # 기존 JSON 내용 가져오기
            json_content = self.get_json_content(filename)
            
            # situations 업데이트
            json_content['situations'] = situations
            json_content['updated_at'] = datetime.now().isoformat()
            
            # 업데이트된 JSON을 S3에 다시 업로드
            s3_url = self.upload_json(json_content, filename)
            
            print(f"✅ JSON situations 업데이트 완료: {filename}")
            return s3_url
            
        except Exception as e:
            print(f"❌ JSON situations 업데이트 실패: {filename} - {e}")
            logger.error(f"JSON situations 업데이트 실패: {filename} - {e}")
            raise Exception(f"JSON situations 업데이트 실패: {str(e)}")
    
    def delete_image(self, s3_url: str) -> bool:
        """S3에서 이미지 삭제"""
        try:
            if not self.s3_client:
                raise Exception("S3 클라이언트가 초기화되지 않았습니다.")
            
            # URL에서 키 추출
            key = s3_url.replace(f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/", "")
            
            # S3에서 삭제
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            print(f"✅ S3 삭제 성공: {key}")
            return True
            
        except Exception as e:
            print(f"❌ S3 삭제 실패: {e}")
            logger.error(f"S3 삭제 실패: {e}")
            return False
    
    def get_image_url(self, s3_key: str) -> str:
        """S3 키로부터 이미지 URL 생성"""
        return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    
    def fix_image_content_type(self, s3_key: str) -> bool:
        """이미지 파일의 ContentType을 올바르게 수정"""
        try:
            if not self.s3_client:
                return False
            
            # 파일 확장자 추출
            file_extension = s3_key.split('.')[-1].lower()
            
            # ContentType 매핑
            content_type_mapping = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp',
                'gif': 'image/gif'
            }
            content_type = content_type_mapping.get(file_extension, 'image/jpeg')
            
            # 기존 객체 복사 (ContentType 변경)
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': s3_key
            }
            
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource=copy_source,
                Key=s3_key,
                MetadataDirective='REPLACE',
                ContentType=content_type
            )
            
            print(f"✅ ContentType 수정 완료: {s3_key} -> {content_type}")
            return True
            
        except Exception as e:
            print(f"❌ ContentType 수정 실패: {s3_key} - {e}")
            return False

# 전역 S3 서비스 인스턴스
s3_service = None
try:
    s3_service = S3Service()
except Exception as e:
    print(f"❌ 전역 S3 서비스 초기화 실패: {e}")
    s3_service = None 