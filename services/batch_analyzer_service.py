import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from services.s3_service import s3_service
from services.claude_vision_service import claude_vision_service
from services.fashion_expert_service import get_fashion_expert_service
from services.outfit_analyzer_service import OutfitAnalyzerService
from api.fashion_routes import ImageAnalysisRequest

logger = logging.getLogger(__name__)

class BatchAnalyzerService:
    """배치 이미지 분석을 담당하는 서비스 클래스"""
    
    def __init__(self):
        self.s3_service = s3_service
        self.claude_vision_service = claude_vision_service
        self.outfit_analyzer = OutfitAnalyzerService()
        
    def get_files_to_analyze(self) -> List[Dict[str, str]]:
        """분석할 파일 목록을 가져옵니다 (JSON이 없는 이미지들)"""
        if not self.s3_service:
            raise Exception("S3 서비스가 초기화되지 않았습니다.")
        
        return self.s3_service.get_files_without_json()
    
    def fix_image_content_type_if_needed(self, s3_key: str) -> None:
        """이미지의 ContentType을 수정합니다 (필요한 경우)"""
        if not self.s3_service:
            return
            
        try:
            # S3에서 파일의 ContentType 확인
            response = self.s3_service.s3_client.head_object(
                Bucket=self.s3_service.bucket_name,
                Key=s3_key
            )
            content_type = response.get('ContentType', '')
            
            # ContentType이 잘못된 경우 수정
            if content_type == 'binary/octet-stream' or not content_type.startswith('image/'):
                print(f"⚠️ ContentType 수정 중: {content_type} -> image/jpeg")
                self.s3_service.fix_image_content_type(s3_key)
        except Exception as e:
            print(f"⚠️ ContentType 확인 실패: {e}")
    
    async def analyze_single_file(self, file_info: Dict[str, str]) -> Tuple[bool, Dict[str, Any]]:
        """단일 파일을 분석합니다"""
        try:
            print(f"🔍 파일 분석 중: {file_info['filename']}")
            
            # ContentType 문제가 있는 경우 수정 시도
            self.fix_image_content_type_if_needed(file_info['s3_key'])
            
            # 새로운 OutfitAnalyzerService를 사용하여 분석 수행
            result = await self.outfit_analyzer.analyze_outfit_from_url(
                image_url=file_info['s3_url'],
                room_id=None,  # 배치 처리시 room_id는 None
                prompt=None
            )
            
            if result["success"]:
                return True, {
                    "filename": file_info['filename'],
                    "s3_url": file_info['s3_url'],
                    "analysis_result": result["data"]
                }
            else:
                return False, {
                    "filename": file_info['filename'],
                    "s3_url": file_info['s3_url'],
                    "error": result["message"]
                }
                
        except Exception as e:
            print(f"❌ 파일 분석 중 에러 발생: {file_info['filename']} - {str(e)}")
            return False, {
                "filename": file_info['filename'],
                "s3_url": file_info['s3_url'],
                "error": str(e)
            }
    
    async def analyze_batch(self) -> Dict[str, Any]:
        """배치 이미지 분석을 수행합니다"""
        print(f"🔍 batch_analyze_images 호출됨")
        print(f"🔍 s3_service 상태: {self.s3_service is not None}")
        
        # S3 서비스 초기화 확인
        if not self.s3_service:
            print("❌ s3_service가 None입니다!")
            raise Exception("S3 서비스가 초기화되지 않았습니다.")
        
        try:
            # JSON이 없는 이미지 파일들 조회
            files_to_analyze = self.get_files_to_analyze()
            
            if not files_to_analyze:
                return {
                    "total_files": 0,
                    "analyzed_files": [],
                    "failed_files": []
                }
            
            print(f"🔍 분석 대상 파일 수: {len(files_to_analyze)}")
            
            analyzed_files = []
            failed_files = []
            
            # 각 파일에 대해 분석 수행
            for file_info in files_to_analyze:
                success, result = await self.analyze_single_file(file_info)
                
                if success:
                    analyzed_files.append(result)
                    print(f"✅ 파일 분석 완료: {file_info['filename']}")
                else:
                    failed_files.append(result)
                    print(f"❌ 파일 분석 실패: {file_info['filename']} - {result.get('error', 'Unknown error')}")
            
            return {
                "total_files": len(files_to_analyze),
                "analyzed_files": analyzed_files,
                "failed_files": failed_files,
                "success_count": len(analyzed_files),
                "failure_count": len(failed_files)
            }
            
        except Exception as e:
            print(f"❌ 배치 분석 에러 발생: {str(e)}")
            logger.error(f"배치 분석 실패: {str(e)}")
            raise Exception(f"배치 분석 실패: {str(e)}") 