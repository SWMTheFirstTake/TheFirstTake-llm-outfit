#!/usr/bin/env python3
"""
S3 배치 이미지 분석 스크립트
기존 /batch-analyze API 로직을 독립적으로 실행
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import json
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 설정 (실행 전에 설정하거나 여기서 직접 설정)
os.environ.setdefault('AWS_ACCESS_KEY', '')
os.environ.setdefault('AWS_SECRET_KEY', '')
os.environ.setdefault('AWS_REGION', 'ap-northeast-2')
os.environ.setdefault('S3_COMBINATION_BUCKET_NAME', 'thefirsttake-combination')
os.environ.setdefault('S3_COMBINATION_BUCKET_IMAGE_PREFIX', 'image')
os.environ.setdefault('S3_COMBINATION_BUCKET_JSON_PREFIX', 'json')
os.environ.setdefault('CLAUDE_API_KEY', '')  # 실제 API 키로 변경 필요

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 필요한 모듈들 import
try:
    from config import settings
    from services.s3_service import S3Service
    from services.claude_vision_service import ClaudeVisionService
    from api.fashion_routes import ImageAnalysisRequest
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("프로젝트 루트 디렉토리에서 실행해주세요.")
    sys.exit(1)

class BatchAnalyzer:
    def __init__(self):
        """배치 분석기 초기화"""
        self.s3_service = S3Service()
        self.vision_service = ClaudeVisionService()
        
    async def analyze_outfit(self, request: ImageAnalysisRequest) -> Dict[str, Any]:
        """기존 analyze_outfit 함수 로직"""
        try:
            print(f"🔍 analyze_outfit 호출됨 (S3 링크)")
            print(f"🔍 claude_vision_service 상태: {self.vision_service is not None}")
            print(f"🔍 이미지 URL: {request.image_url}")
            
            # S3 이미지 링크 분석
            print(f"🔍 S3 이미지 링크 분석 시작: {request.image_url}")
            
            # Claude Vision API 호출
            analysis_result = await self.vision_service.analyze_outfit(
                image_url=request.image_url,
                prompt=request.prompt
            )
            
            if not analysis_result:
                raise Exception("Claude Vision API 분석 결과가 없습니다.")
            
            # JSON 파일명 생성 (이미지 파일명 기반)
            image_filename = request.image_url.split('/')[-1].split('.')[0]
            
            # 로컬 저장 디렉토리 생성
            local_dir = "/home/ubuntu/fashion_summary/item"
            os.makedirs(local_dir, exist_ok=True)
            
            # 로컬 JSON 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"{timestamp}.json"
            local_filepath = os.path.join(local_dir, local_filename)
            
            # 상황 태그 추출 (기존 로직과 동일)
            situations = []
            if "extracted_items" in analysis_result:
                items = analysis_result["extracted_items"]
                
                # 상의가 있는 경우
                if "top" in items and items["top"].get("item"):
                    if "셔츠" in items["top"]["item"] or "블라우스" in items["top"]["item"]:
                        situations.extend(["비즈니스", "데이트", "소개팅"])
                    elif "티셔츠" in items["top"]["item"]:
                        situations.extend(["일상", "캐주얼", "데이트"])
                    elif "니트" in items["top"]["item"] or "스웨터" in items["top"]["item"]:
                        situations.extend(["일상", "데이트", "가을", "겨울"])
                
                # 하의가 있는 경우
                if "bottom" in items and items["bottom"].get("item"):
                    if "슬랙스" in items["bottom"]["item"]:
                        situations.extend(["비즈니스", "데이트", "소개팅"])
                    elif "데님" in items["bottom"]["item"] or "청바지" in items["bottom"]["item"]:
                        situations.extend(["일상", "캐주얼", "데이트"])
                    elif "트레이닝" in items["bottom"]["item"]:
                        situations.extend(["일상", "운동", "캐주얼"])
                
                # 신발이 있는 경우
                if "shoes" in items and items["shoes"].get("item"):
                    if "로퍼" in items["shoes"]["item"] or "옥스포드" in items["shoes"]["item"]:
                        situations.extend(["비즈니스", "데이트"])
                    elif "스니커즈" in items["shoes"]["item"]:
                        situations.extend(["일상", "캐주얼", "운동"])
            
            # 중복 제거
            situations = list(set(situations))
            
            # 분석 결과에 상황 태그 추가
            analysis_result["situations"] = situations
            analysis_result["source_image_url"] = request.image_url
            analysis_result["analyzed_at"] = datetime.now().isoformat()
            
            # 로컬에 JSON 저장
            with open(local_filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 로컬 JSON 저장 완료: {local_filepath}")
            
            # S3에 JSON 업로드 (기존 파일이 없는 경우에만)
            if not self.s3_service.check_json_exists(image_filename):
                s3_json_url = self.s3_service.upload_json(analysis_result, image_filename)
                print(f"✅ S3 JSON 업로드 완료: {s3_json_url}")
            else:
                print(f"⚠️ S3에 이미 JSON 파일이 존재함: {image_filename}")
            
            return {
                "success": True,
                "data": analysis_result.get("extracted_items", {}),
                "local_file": local_filepath,
                "s3_json_url": f"https://{settings.S3_COMBINATION_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{settings.S3_COMBINATION_BUCKET_JSON_PREFIX}/{image_filename}.json"
            }
            
        except Exception as e:
            print(f"❌ S3 이미지 분석 실패: {e}")
            logger.error(f"이미지 분석 실패: {e}")
            raise Exception(f"S3 이미지 분석 실패: {str(e)}")
    
    async def batch_analyze_images(self) -> Dict[str, Any]:
        """기존 batch_analyze_images 함수 로직"""
        try:
            print("🚀 배치 이미지 분석 시작...")
            
            # S3에서 이미지 파일 목록 가져오기
            image_files = self.s3_service.list_image_files()
            print(f"📁 S3에서 {len(image_files)}개의 이미지 파일 발견")
            
            if not image_files:
                return {
                    "success": True,
                    "message": "분석할 이미지 파일이 없습니다.",
                    "total_files": 0,
                    "processed_files": [],
                    "failed_files": []
                }
            
            # JSON이 없는 파일들만 필터링
            files_to_analyze = []
            for file_info in image_files:
                filename = file_info['filename']
                if not self.s3_service.check_json_exists(filename):
                    files_to_analyze.append(file_info)
                else:
                    print(f"⏭️ JSON 이미 존재: {filename}")
            
            print(f"🔍 분석 대상: {len(files_to_analyze)}개 파일")
            
            if not files_to_analyze:
                return {
                    "success": True,
                    "message": "모든 이미지에 대해 JSON 분석이 완료되었습니다.",
                    "total_files": len(image_files),
                    "processed_files": [],
                    "failed_files": []
                }
            
            # 각 파일에 대해 분석 수행
            processed_files = []
            failed_files = []
            
            for file_info in files_to_analyze:
                try:
                    print(f"🔍 파일 분석 중: {file_info['filename']}")
                    
                    # ContentType 문제가 있는 경우 수정 시도
                    if self.s3_service:
                        try:
                            # S3에서 파일의 ContentType 확인
                            response = self.s3_service.s3_client.head_object(
                                Bucket=self.s3_service.bucket_name,
                                Key=file_info['s3_key']
                            )
                            content_type = response.get('ContentType', '')
                            
                            # ContentType이 잘못된 경우 수정
                            if content_type == 'binary/octet-stream' or not content_type.startswith('image/'):
                                print(f"⚠️ ContentType 수정 중: {content_type} -> image/jpeg")
                                self.s3_service.fix_image_content_type(file_info['s3_key'])
                        except Exception as e:
                            print(f"⚠️ ContentType 확인 실패: {e}")
                    
                    # ImageAnalysisRequest 객체 생성
                    request_data = ImageAnalysisRequest(
                        image_url=file_info['s3_url'],
                        room_id=None,  # 배치 처리시 room_id는 None
                        prompt=None
                    )
                    
                    # 내부적으로 analyze_outfit 함수 호출
                    result = await self.analyze_outfit(request_data)
                    
                    processed_files.append({
                        "filename": file_info['filename'],
                        "s3_url": file_info['s3_url'],
                        "result": result
                    })
                    
                    print(f"✅ 분석 완료: {file_info['filename']}")
                    
                except Exception as e:
                    print(f"❌ 파일 분석 중 에러 발생: {file_info['filename']} - {e}")
                    failed_files.append({
                        "filename": file_info['filename'],
                        "s3_url": file_info['s3_url'],
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "message": f"배치 분석 완료. 성공: {len(processed_files)}개, 실패: {len(failed_files)}개",
                "total_files": len(image_files),
                "processed_files": processed_files,
                "failed_files": failed_files
            }
            
        except Exception as e:
            print(f"❌ 배치 분석 중 에러 발생: {e}")
            logger.error(f"배치 분석 실패: {e}")
            return {
                "success": False,
                "message": f"배치 분석 실패: {str(e)}",
                "total_files": 0,
                "processed_files": [],
                "failed_files": []
            }

async def main():
    """메인 실행 함수"""
    print("🎯 S3 배치 이미지 분석 스크립트 시작")
    print("=" * 50)
    
    # Claude API 키 확인
    if not os.getenv('CLAUDE_API_KEY') or os.getenv('CLAUDE_API_KEY') == 'your_claude_api_key_here':
        print("❌ Claude API 키가 설정되지 않았습니다.")
        print("스크립트 상단의 CLAUDE_API_KEY를 실제 키로 변경해주세요.")
        return
    
    try:
        # 배치 분석기 생성 및 실행
        analyzer = BatchAnalyzer()
        result = await analyzer.batch_analyze_images()
        
        print("\n" + "=" * 50)
        print("📊 분석 결과 요약")
        print("=" * 50)
        print(f"성공 여부: {result['success']}")
        print(f"메시지: {result['message']}")
        print(f"전체 파일 수: {result['total_files']}")
        print(f"처리된 파일 수: {len(result['processed_files'])}")
        print(f"실패한 파일 수: {len(result['failed_files'])}")
        
        if result['processed_files']:
            print(f"\n✅ 성공한 파일들:")
            for file_info in result['processed_files']:
                print(f"  - {file_info['filename']}")
        
        if result['failed_files']:
            print(f"\n❌ 실패한 파일들:")
            for file_info in result['failed_files']:
                print(f"  - {file_info['filename']}: {file_info['error']}")
        
        print("\n🎉 배치 분석 완료!")
        
    except Exception as e:
        print(f"❌ 스크립트 실행 중 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main()) 