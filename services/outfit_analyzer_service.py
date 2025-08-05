import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.claude_vision_service import claude_vision_service
from services.fashion_expert_service import get_fashion_expert_service
from services.s3_service import s3_service
from services.utils import save_outfit_analysis_to_json, analyze_situations_from_outfit

logger = logging.getLogger(__name__)

class OutfitAnalyzerService:
    """착장 분석을 담당하는 서비스 클래스"""
    
    def __init__(self):
        self.claude_vision_service = claude_vision_service
        self.s3_service = s3_service
        
    async def analyze_outfit_from_url(self, image_url: str, room_id: Optional[str] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
        """S3 이미지 링크 기반 착장 분석"""
        
        print(f"🔍 analyze_outfit_from_url 호출됨 (S3 링크)")
        print(f"🔍 claude_vision_service 상태: {self.claude_vision_service is not None}")
        print(f"🔍 이미지 URL: {image_url}")
        
        # 서비스 초기화 확인
        if self.claude_vision_service is None:
            raise Exception("Claude Vision 서비스가 초기화되지 않았습니다.")
        
        try:
            # S3 이미지 링크 분석
            image_analysis = self.claude_vision_service.analyze_outfit_from_url(
                image_url=image_url,
                prompt=prompt
            )
            print("✅ Claude API 호출 완료")
            
            # 패션 데이터와 매칭
            fashion_expert_service = get_fashion_expert_service()
            if fashion_expert_service:
                matched_result = await fashion_expert_service.analyze_image_with_fashion_data(image_analysis)
                extracted_items = matched_result["extracted_items"]
            else:
                # 패션 데이터 매칭 없이 기본 분석만 반환
                extracted_items = image_analysis
            
            # JSON 파일로 저장 (로컬)
            saved_filepath = save_outfit_analysis_to_json(extracted_items, room_id=room_id)
            
            # S3에 JSON 업로드 (이미지 파일명 기반)
            s3_json_url = None
            if self.s3_service:
                try:
                    # 이미지 URL에서 파일명 추출
                    image_filename = image_url.split('/')[-1].split('.')[0]  # 확장자 제거
                    
                    # JSON 파일이 이미 존재하는지 확인
                    if not self.s3_service.check_json_exists(image_filename):
                        # JSON 데이터 준비
                        json_data = {
                            "extracted_items": extracted_items,
                            "situations": analyze_situations_from_outfit(extracted_items),
                            "analysis_timestamp": datetime.now().isoformat(),
                            "room_id": room_id,
                            "source_image_url": image_url
                        }
                        
                        # S3에 JSON 업로드
                        s3_json_url = self.s3_service.upload_json(json_data, image_filename)
                        print(f"✅ S3 JSON 업로드 완료: {s3_json_url}")
                    else:
                        print(f"ℹ️ JSON 파일이 이미 존재합니다: {image_filename}")
                        
                except Exception as e:
                    print(f"❌ S3 JSON 업로드 실패: {e}")
            
            return {
                "success": True,
                "message": "이미지 분석 및 패션 데이터 매칭이 성공적으로 완료되었습니다",
                "data": {
                    "extracted_items": extracted_items,
                    "s3_json_url": s3_json_url
                }
            }
            
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            logger.error(f"이미지 분석 실패: {str(e)}")
            raise Exception(f"분석 실패: {str(e)}")
    
    async def analyze_outfit_from_bytes(self, image_bytes: bytes, filename: str, room_id: Optional[str] = None, prompt: Optional[str] = None) -> Dict[str, Any]:
        """이미지 바이트 기반 착장 분석"""
        
        print(f"🔍 analyze_outfit_from_bytes 호출됨")
        print(f"🔍 claude_vision_service 상태: {self.claude_vision_service is not None}")
        print(f"🔍 파일명: {filename}")
        
        # 서비스 초기화 확인
        if self.claude_vision_service is None:
            raise Exception("Claude Vision 서비스가 초기화되지 않았습니다.")
        
        try:
            # 이미지 바이트 분석
            image_analysis = self.claude_vision_service.analyze_outfit(
                image_bytes=image_bytes,
                filename=filename
            )
            print("✅ Claude API 호출 완료")
            
            # 패션 데이터와 매칭
            fashion_expert_service = get_fashion_expert_service()
            if fashion_expert_service:
                matched_result = await fashion_expert_service.analyze_image_with_fashion_data(image_analysis)
                extracted_items = matched_result["extracted_items"]
            else:
                # 패션 데이터 매칭 없이 기본 분석만 반환
                extracted_items = image_analysis
            
            # JSON 파일로 저장 (로컬)
            saved_filepath = save_outfit_analysis_to_json(extracted_items, room_id=room_id)
            
            # S3에 JSON 업로드 (파일명 기반)
            s3_json_url = None
            if self.s3_service:
                try:
                    # 파일명에서 확장자 제거
                    image_filename = filename.split('.')[0]
                    
                    # JSON 파일이 이미 존재하는지 확인
                    if not self.s3_service.check_json_exists(image_filename):
                        # JSON 데이터 준비
                        json_data = {
                            "extracted_items": extracted_items,
                            "situations": analyze_situations_from_outfit(extracted_items),
                            "analysis_timestamp": datetime.now().isoformat(),
                            "room_id": room_id,
                            "source_filename": filename
                        }
                        
                        # S3에 JSON 업로드
                        s3_json_url = self.s3_service.upload_json(json_data, image_filename)
                        print(f"✅ S3 JSON 업로드 완료: {s3_json_url}")
                    else:
                        print(f"ℹ️ JSON 파일이 이미 존재합니다: {image_filename}")
                        
                except Exception as e:
                    print(f"❌ S3 JSON 업로드 실패: {e}")
            
            return {
                "success": True,
                "message": "이미지 분석 및 패션 데이터 매칭이 성공적으로 완료되었습니다",
                "data": {
                    "extracted_items": extracted_items,
                    "s3_json_url": s3_json_url
                }
            }
            
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            logger.error(f"이미지 분석 실패: {str(e)}")
            raise Exception(f"분석 실패: {str(e)}") 