import anthropic
import base64
import requests
from urllib.parse import urlparse

class ClaudeVisionService:
    def __init__(self, api_key: str):
        # API 키 상태 확인
        print(f"🔍 ClaudeVisionService API 키 상태: {'설정됨' if api_key else '설정되지 않음'}")
        print(f"🔍 ClaudeVisionService API 키 길이: {len(api_key) if api_key else 0}")
        
        if not api_key:
            raise ValueError("ClaudeVisionService: API 키가 설정되지 않았습니다.")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        print(f"🔍 ClaudeVisionService 초기화 완료")

    def analyze_outfit_from_url(self, image_url: str, prompt: str = None) -> str:
        """S3 이미지 링크로부터 착장 분석"""
        try:
            print(f"🔍 S3 이미지 링크 분석 시작: {image_url}")
            
            # URL 유효성 검증
            if not self._is_valid_image_url(image_url):
                raise ValueError("유효하지 않은 이미지 URL입니다.")
            
            # 이미지 다운로드
            image_bytes = self._download_image(image_url)
            print(f"✅ 이미지 다운로드 완료: {len(image_bytes)} bytes")
            
            # 파일명 추출 (확장자 감지용)
            filename = self._extract_filename_from_url(image_url)
            
            # 기존 analyze_outfit 메서드 호출
            return self.analyze_outfit(image_bytes, filename=filename, prompt=prompt)
            
        except Exception as e:
            print(f"❌ S3 이미지 분석 실패: {str(e)}")
            raise Exception(f"S3 이미지 분석 실패: {str(e)}")

    def _is_valid_image_url(self, url: str) -> bool:
        """이미지 URL 유효성 검증"""
        try:
            parsed = urlparse(url)
            # S3 URL 또는 일반적인 이미지 URL 패턴 확인
            valid_domains = ['s3.amazonaws.com', 's3.', '.amazonaws.com']
            is_s3_url = any(domain in parsed.netloc for domain in valid_domains)
            
            # 파일 확장자 확인
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            has_valid_extension = any(url.lower().endswith(ext) for ext in valid_extensions)
            
            return is_s3_url or has_valid_extension
        except Exception:
            return False

    def _download_image(self, url: str) -> bytes:
        """이미지 다운로드"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Content-Type 확인
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"이미지 파일이 아닙니다: {content_type}")
            
            return response.content
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"이미지 다운로드 실패: {str(e)}")

    def _extract_filename_from_url(self, url: str) -> str:
        """URL에서 파일명 추출"""
        try:
            parsed = urlparse(url)
            path = parsed.path
            filename = path.split('/')[-1]
            return filename if filename else 'image.jpg'
        except Exception:
            return 'image.jpg'

    def analyze_outfit(self, image_bytes: bytes, filename: str = None, content_type: str = None, prompt: str = None) -> str:
        try:
            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # 파일 타입 자동 감지
            media_type = self._detect_media_type(image_bytes, filename, content_type)
            
            print(f"🔍 이미지 전송: {len(image_bytes)} bytes, 타입: {media_type}")
            
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt or "이 이미지의 착장을 간결하게 분석해줘. 주요 아이템명, 색상, 스타일을 한 줄로 요약해줘."
                            }
                        ]
                    }
                ]
            )
            return message.content[0].text
            
        except Exception as e:
            print(f"❌ Claude API 호출 실패: {str(e)}")
            raise Exception(f"Claude API 호출 실패: {str(e)}")
    
    def _detect_media_type(self, image_bytes: bytes, filename: str = None, content_type: str = None) -> str:
        """이미지 타입 자동 감지"""
        
        # 1. content_type이 있으면 사용
        if content_type and content_type in ['image/jpeg', 'image/png', 'image/webp', 'image/gif']:
            return content_type
        
        # 2. 파일명 확장자로 판단
        if filename:
            filename_lower = filename.lower()
            if filename_lower.endswith(('.jpg', '.jpeg')):
                return "image/jpeg"
            elif filename_lower.endswith('.png'):
                return "image/png"
            elif filename_lower.endswith('.webp'):
                return "image/webp"
            elif filename_lower.endswith('.gif'):
                return "image/gif"
        
        # 3. 바이트 헤더로 판단
        if image_bytes.startswith(b'\xff\xd8\xff'):  # JPEG
            return "image/jpeg"
        elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return "image/png"
        elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:12]:  # WebP
            return "image/webp"
        elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):  # GIF
            return "image/gif"
        
        # 4. 기본값
        return "image/jpeg"