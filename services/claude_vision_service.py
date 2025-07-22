import anthropic
import base64

class ClaudeVisionService:
    def __init__(self, api_key: str):
        # API 키 상태 확인
        print(f"🔍 ClaudeVisionService API 키 상태: {'설정됨' if api_key else '설정되지 않음'}")
        print(f"🔍 ClaudeVisionService API 키 길이: {len(api_key) if api_key else 0}")
        
        if not api_key:
            raise ValueError("ClaudeVisionService: API 키가 설정되지 않았습니다.")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        print(f"🔍 ClaudeVisionService 초기화 완료")

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
                                "text": prompt or "이 이미지의 착장(색상, 아이템, 스타일, 계절감 등)을 한국어로 상세히 분석해줘."
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