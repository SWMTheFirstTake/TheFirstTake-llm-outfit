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
            
            # 간소화된 패션 분석 프롬프트 (필요한 정보만 추출)
            default_prompt = """이 이미지를 분석하여 다음 JSON 형식으로만 응답해주세요. 사진에서 보이지 않는 아이템은 가장 어울릴 것 같은 아이템을 추천해주세요:

{
  "top": {
    "item": "아이템명 (예: 베이직 버튼다운 긴팔 셔츠, 린넨 반팔 셔츠, 니트 긴팔 스웨터)",
    "color": "간소화된 색상명 (예: 브라운, 블랙, 화이트, 네이비, 베이지, 그레이)",
    "fit": "핏감 (오버핏, 레귤러핏, 슬림핏 등)",
    "material": "소재 (린넨, 면, 니트 등)",
    "length": "길이 (허리선 기준으로 어느 정도까지 내려오는지)"
  },
  "bottom": {
    "item": "아이템명 (예: 와이드 슬랙스, 와이드 팬츠)",
    "color": "간소화된 색상명 (예: 블랙, 화이트, 네이비, 베이지, 그레이)", 
    "fit": "핏감 (와이드핏, 스키니핏, 레귤러핏 등)",
    "material": "소재 (린넨, 면, 데님 등)",
    "length": "길이 (바지 길이, 기장 등)"
  },
  "shoes": {
    "item": "아이템명 (예: 캔버스 스니커즈, 로퍼, 샌들)",
    "color": "간소화된 색상명 (예: 화이트, 블랙, 브라운)",
    "style": "스타일 (캐주얼, 포멀 등)"
  },
  "accessories": [
    {
      "item": "아이템명 (예: 비즈 목걸이, 캡, 가방)",
      "color": "간소화된 색상명 (예: 골드, 실버, 블랙)"
    }
  ],
  "styling_methods": {
    "top_wearing_method": "상의 착용법 (상의를 하의에 완전히 넣었는지, 일부만 넣었는지, 아예 안 넣었는지)",
    "tuck_degree": "상의 넣는 정도 (전체 넣기, 앞부분만 넣기, 옆부분만 넣기, 아예 안 넣기)",
    "fit_details": "핏감 상세 (어깨, 가슴, 허리, 엉덩이 부분의 핏감)",
    "silhouette_balance": "실루엣 밸런스 (상하의 길이 비율, 전체적인 균형감)",
    "styling_points": "스타일링 포인트 (롤업, 버튼 상태, 주머니 활용 등)"
  }
}

주의사항:
1. 사진에서 보이지 않는 아이템(신발, 액세서리 등)은 전체 룩과 가장 어울릴 것 같은 아이템을 추천해주세요
2. 색상은 간소화된 색상명을 사용해주세요 (예: 카키브라운 → 브라운, 차콜블랙 → 블랙, 네이비블루 → 네이비)
3. 상의 아이템명에는 반드시 소매 길이를 포함해주세요 (긴팔, 반팔, 민소매 등)
4. 핏감과 소재는 가능한 한 구체적으로 분석해주세요
5. 스타일링 방법은 상의를 하의에 넣는 정도를 정확히 파악해주세요
6. 반드시 JSON 형식으로만 응답해주세요"""
            
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1500,
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
                                "text": prompt or default_prompt
                            }
                        ]
                    }
                ]
            )
            
            # JSON 응답 파싱
            response_text = message.content[0].text
            try:
                # JSON 부분만 추출 (```json``` 블록이 있는 경우)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text.strip()
                
                # JSON 파싱
                import json
                parsed_data = json.loads(json_text)
                return parsed_data
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 실패: {e}")
                print(f"응답 텍스트: {response_text}")
                # 파싱 실패시 원본 텍스트 반환
                return {"error": "JSON 파싱 실패", "raw_response": response_text}
            
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