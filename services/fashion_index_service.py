import json
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime
from services.redis_service import redis_service
from services.s3_service import s3_service

logger = logging.getLogger(__name__)

class FashionIndexService:
    """패션 데이터 인덱싱 및 빠른 검색을 위한 서비스"""
    
    def __init__(self):
        self.index_prefix = "fashion_index"
        self.metadata_prefix = "fashion_metadata"
        
    def build_indexes(self, force_rebuild: bool = False) -> Dict[str, int]:
        """S3의 모든 JSON 파일을 분석하여 인덱스 구축"""
        print("🔍 패션 인덱스 구축 시작...")
        
        if force_rebuild:
            print("🔄 강제 재구축 모드: 기존 인덱스 완전 삭제")
            self._clear_indexes()
            return self._build_all_indexes()
        else:
            print("🔄 증분 업데이트 모드: 새로운 파일만 인덱싱")
            return self._build_incremental_indexes()
    
    def _build_all_indexes(self) -> Dict[str, int]:
        """전체 인덱스 재구축"""
        try:
            # S3에서 모든 JSON 파일 가져오기
            json_files = s3_service.list_json_files()
            if not json_files:
                print("❌ S3에 JSON 파일이 없습니다!")
                return {"total": 0, "indexed": 0}
            
            indexed_count = 0
            total_count = len(json_files)
            
            for file_info in json_files:
                try:
                    # JSON 내용 가져오기
                    json_content = s3_service.get_json_content(file_info['filename'])
                    
                    # 인덱스 구축
                    self._index_file(file_info['filename'], json_content, file_info['s3_url'])
                    indexed_count += 1
                    
                    if indexed_count % 10 == 0:
                        print(f"   📊 진행률: {indexed_count}/{total_count}")
                        
                except Exception as e:
                    print(f"❌ 파일 인덱싱 실패: {file_info['filename']} - {e}")
                    continue
            
            print(f"✅ 전체 인덱스 구축 완료: {indexed_count}/{total_count}개 파일")
            return {"total": total_count, "indexed": indexed_count}
            
        except Exception as e:
            print(f"❌ 전체 인덱스 구축 실패: {e}")
            logger.error(f"전체 인덱스 구축 실패: {e}")
            return {"total": 0, "indexed": 0}
    
    def _build_incremental_indexes(self) -> Dict[str, int]:
        """증분 인덱스 업데이트 (새로운 파일만)"""
        try:
            # S3에서 모든 JSON 파일 가져오기
            s3_files = s3_service.list_json_files()
            if not s3_files:
                print("❌ S3에 JSON 파일이 없습니다!")
                return {"total": 0, "indexed": 0, "updated": 0}
            
            # Redis에 이미 인덱싱된 파일들 확인
            existing_metadata_keys = redis_service.keys(f"{self.metadata_prefix}:*")
            existing_files = set()
            for key in existing_metadata_keys:
                filename = key.replace(f"{self.metadata_prefix}:", "")
                existing_files.add(filename)
            
            print(f"📊 기존 인덱싱된 파일: {len(existing_files)}개")
            print(f"📊 S3 전체 파일: {len(s3_files)}개")
            
            # 새로운 파일들 찾기
            s3_filenames = {file_info['filename'] for file_info in s3_files}
            new_files = s3_filenames - existing_files
            updated_files = set()
            
            print(f"🆕 새로 추가된 파일: {len(new_files)}개")
            
            # 새로운 파일들 인덱싱
            indexed_count = 0
            for file_info in s3_files:
                if file_info['filename'] in new_files:
                    try:
                        # JSON 내용 가져오기
                        json_content = s3_service.get_json_content(file_info['filename'])
                        
                        # 인덱스 구축
                        self._index_file(file_info['filename'], json_content, file_info['s3_url'])
                        indexed_count += 1
                        
                        if indexed_count % 5 == 0:
                            print(f"   📊 새 파일 인덱싱 진행률: {indexed_count}/{len(new_files)}")
                            
                    except Exception as e:
                        print(f"❌ 새 파일 인덱싱 실패: {file_info['filename']} - {e}")
                        continue
            
            # 기존 파일들의 업데이트 확인 (타임스탬프 비교)
            for file_info in s3_files:
                if file_info['filename'] in existing_files:
                    try:
                        # 기존 메타데이터 조회
                        existing_metadata = redis_service.get_json(f"{self.metadata_prefix}:{file_info['filename']}")
                        if existing_metadata:
                            existing_timestamp = existing_metadata.get('timestamp', '')
                            
                            # S3 파일의 최신 타임스탬프 확인
                            json_content = s3_service.get_json_content(file_info['filename'])
                            s3_timestamp = json_content.get('analysis_timestamp', '')
                            
                            # 타임스탬프가 다르면 업데이트
                            if existing_timestamp != s3_timestamp:
                                self._index_file(file_info['filename'], json_content, file_info['s3_url'])
                                updated_files.add(file_info['filename'])
                                
                    except Exception as e:
                        print(f"❌ 파일 업데이트 확인 실패: {file_info['filename']} - {e}")
                        continue
            
            print(f"✅ 증분 인덱스 업데이트 완료:")
            print(f"   - 새로 인덱싱된 파일: {len(new_files)}개")
            print(f"   - 업데이트된 파일: {len(updated_files)}개")
            print(f"   - 총 처리된 파일: {len(new_files) + len(updated_files)}개")
            
            return {
                "total": len(s3_files),
                "indexed": len(new_files),
                "updated": len(updated_files),
                "existing": len(existing_files)
            }
            
        except Exception as e:
            print(f"❌ 증분 인덱스 업데이트 실패: {e}")
            logger.error(f"증분 인덱스 업데이트 실패: {e}")
            return {"total": 0, "indexed": 0, "updated": 0}
    
    def _index_file(self, filename: str, content: dict, s3_url: str):
        """단일 파일을 인덱싱"""
        try:
            extracted_items = content.get('extracted_items', {})
            situations = content.get('situations', [])
            
            # 메타데이터 저장
            metadata = {
                "filename": filename,
                "s3_url": s3_url,
                "situations": situations,
                "items": self._extract_item_summary(extracted_items),
                "styling_methods": extracted_items.get('styling_methods', {}),
                "timestamp": content.get('analysis_timestamp', ''),
                "updated_at": content.get('updated_at', '')
            }
            
            # Redis에 메타데이터 저장
            redis_service.set_json(f"{self.metadata_prefix}:{filename}", metadata)
            
            # 상황별 인덱스
            for situation in situations:
                self._add_to_index(f"situation:{situation}", filename)
            
            # 아이템별 인덱스
            self._index_items(filename, extracted_items)
            
            # 색상별 인덱스
            self._index_colors(filename, extracted_items)
            
            # 스타일링 방법별 인덱스
            self._index_styling_methods(filename, extracted_items)
            
        except Exception as e:
            print(f"❌ 파일 인덱싱 중 에러: {filename} - {e}")
    
    def _extract_item_summary(self, extracted_items: dict) -> dict:
        """아이템 요약 정보 추출"""
        summary = {}
        
        for category, item_info in extracted_items.items():
            if isinstance(item_info, dict):
                summary[category] = {
                    "item": item_info.get('item', ''),
                    "color": item_info.get('color', ''),
                    "fit": item_info.get('fit', ''),
                    "material": item_info.get('material', '')
                }
        
        return summary
    
    def _index_items(self, filename: str, extracted_items: dict):
        """아이템별 인덱스 구축"""
        for category, item_info in extracted_items.items():
            if isinstance(item_info, dict):
                item_name = item_info.get('item', '').lower()
                if item_name:
                    # 아이템명에서 키워드 추출
                    keywords = self._extract_keywords(item_name)
                    for keyword in keywords:
                        self._add_to_index(f"item:{keyword}", filename)
    
    def _index_colors(self, filename: str, extracted_items: dict):
        """색상별 인덱스 구축"""
        colors = set()
        
        for category, item_info in extracted_items.items():
            if isinstance(item_info, dict):
                color = item_info.get('color', '').lower()
                if color:
                    colors.add(color)
        
        for color in colors:
            self._add_to_index(f"color:{color}", filename)
    
    def _index_styling_methods(self, filename: str, extracted_items: dict):
        """스타일링 방법별 인덱스 구축"""
        styling_methods = extracted_items.get('styling_methods', {})
        
        for method_key, method_value in styling_methods.items():
            if isinstance(method_value, str) and method_value:
                keywords = self._extract_keywords(method_value.lower())
                for keyword in keywords:
                    self._add_to_index(f"styling:{keyword}", filename)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 간단한 키워드 추출 (실제로는 더 정교한 NLP 사용 가능)
        keywords = []
        
        # 일반적인 패션 키워드들
        fashion_keywords = [
            "니트", "데님", "가죽", "면", "실크", "울", "폴리에스터",
            "긴팔", "반팔", "와이드", "스키니", "레귤러", "오버핏", "슬림",
            "블랙", "화이트", "그레이", "브라운", "네이비", "베이지",
            "티셔츠", "셔츠", "니트", "스웨터", "후드티", "맨투맨",
            "슬랙스", "청바지", "팬츠", "반바지", "스커트",
            "스니커즈", "로퍼", "옥스포드", "부츠", "샌들",
            "넣기", "턱", "핏", "실루엣", "밸런스"
        ]
        
        for keyword in fashion_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def _add_to_index(self, index_key: str, filename: str):
        """인덱스에 파일 추가"""
        try:
            redis_key = f"{self.index_prefix}:{index_key}"
            redis_service.sadd(redis_key, filename)
        except Exception as e:
            print(f"❌ 인덱스 추가 실패: {index_key} - {e}")
    
    def _clear_indexes(self):
        """기존 인덱스 초기화"""
        try:
            # 인덱스 키들 찾기
            pattern = f"{self.index_prefix}:*"
            keys = redis_service.keys(pattern)
            
            if keys:
                redis_service.delete(*keys)
                print(f"🗑️ 기존 인덱스 {len(keys)}개 삭제")
            
            # 메타데이터 키들 찾기
            pattern = f"{self.metadata_prefix}:*"
            keys = redis_service.keys(pattern)
            
            if keys:
                redis_service.delete(*keys)
                print(f"🗑️ 기존 메타데이터 {len(keys)}개 삭제")
                
        except Exception as e:
            print(f"❌ 인덱스 초기화 실패: {e}")
    
    def search_by_situation(self, situation: str, limit: int = 20) -> List[dict]:
        """상황별 검색"""
        try:
            index_key = f"situation:{situation.lower()}"
            filenames = redis_service.smembers(f"{self.index_prefix}:{index_key}")
            
            results = []
            for filename in list(filenames)[:limit]:
                metadata = self._get_metadata(filename)
                if metadata:
                    results.append(metadata)
            
            return results
        except Exception as e:
            print(f"❌ 상황별 검색 실패: {e}")
            return []
    
    def search_by_item(self, item_keyword: str, limit: int = 20) -> List[dict]:
        """아이템별 검색"""
        try:
            index_key = f"item:{item_keyword.lower()}"
            filenames = redis_service.smembers(f"{self.index_prefix}:{index_key}")
            
            results = []
            for filename in list(filenames)[:limit]:
                metadata = self._get_metadata(filename)
                if metadata:
                    results.append(metadata)
            
            return results
        except Exception as e:
            print(f"❌ 아이템별 검색 실패: {e}")
            return []
    
    def search_by_color(self, color: str, limit: int = 20) -> List[dict]:
        """색상별 검색"""
        try:
            index_key = f"color:{color.lower()}"
            filenames = redis_service.smembers(f"{self.index_prefix}:{index_key}")
            
            results = []
            for filename in list(filenames)[:limit]:
                metadata = self._get_metadata(filename)
                if metadata:
                    results.append(metadata)
            
            return results
        except Exception as e:
            print(f"❌ 색상별 검색 실패: {e}")
            return []
    
    def search_by_styling(self, styling_keyword: str, limit: int = 20) -> List[dict]:
        """스타일링 방법별 검색"""
        try:
            index_key = f"styling:{styling_keyword.lower()}"
            filenames = redis_service.smembers(f"{self.index_prefix}:{index_key}")
            
            results = []
            for filename in list(filenames)[:limit]:
                metadata = self._get_metadata(filename)
                if metadata:
                    results.append(metadata)
            
            return results
        except Exception as e:
            print(f"❌ 스타일링별 검색 실패: {e}")
            return []
    
    def advanced_search(self, criteria: dict, limit: int = 20) -> List[dict]:
        """고급 검색 (여러 조건 조합)"""
        try:
            all_filenames = set()
            first_search = True
            
            # 각 조건별로 검색
            if 'situations' in criteria and criteria['situations']:
                for situation in criteria['situations']:
                    filenames = redis_service.smembers(f"{self.index_prefix}:situation:{situation.lower()}")
                    if first_search:
                        all_filenames = set(filenames)
                        first_search = False
                    else:
                        all_filenames = all_filenames.intersection(set(filenames))
            
            if 'items' in criteria and criteria['items']:
                for item in criteria['items']:
                    filenames = redis_service.smembers(f"{self.index_prefix}:item:{item.lower()}")
                    if first_search:
                        all_filenames = set(filenames)
                        first_search = False
                    else:
                        all_filenames = all_filenames.intersection(set(filenames))
            
            if 'colors' in criteria and criteria['colors']:
                for color in criteria['colors']:
                    filenames = redis_service.smembers(f"{self.index_prefix}:color:{color.lower()}")
                    if first_search:
                        all_filenames = set(filenames)
                        first_search = False
                    else:
                        all_filenames = all_filenames.intersection(set(filenames))
            
            if 'styling' in criteria and criteria['styling']:
                for styling in criteria['styling']:
                    filenames = redis_service.smembers(f"{self.index_prefix}:styling:{styling.lower()}")
                    if first_search:
                        all_filenames = set(filenames)
                        first_search = False
                    else:
                        all_filenames = all_filenames.intersection(set(filenames))
            
            # 검색 조건이 없거나 결과가 없는 경우, 전체 파일에서 랜덤 선택
            if not all_filenames:
                print("⚠️ 검색 조건에 맞는 파일이 없어 전체 파일에서 선택")
                # 전체 메타데이터에서 랜덤 선택
                all_metadata_keys = redis_service.keys(f"{self.metadata_prefix}:*")
                if all_metadata_keys:
                    import random
                    selected_keys = random.sample(all_metadata_keys, min(limit, len(all_metadata_keys)))
                    all_filenames = {key.replace(f"{self.metadata_prefix}:", "") for key in selected_keys}
            
            # 결과 반환
            results = []
            for filename in list(all_filenames)[:limit]:
                metadata = self._get_metadata(filename)
                if metadata:
                    results.append(metadata)
            
            return results
            
        except Exception as e:
            print(f"❌ 고급 검색 실패: {e}")
            return []
    
    def _get_metadata(self, filename: str) -> Optional[dict]:
        """파일 메타데이터 조회"""
        try:
            metadata = redis_service.get_json(f"{self.metadata_prefix}:{filename}")
            return metadata
        except Exception as e:
            print(f"❌ 메타데이터 조회 실패: {filename} - {e}")
            return None
    
    def get_index_stats(self) -> dict:
        """인덱스 통계 정보"""
        try:
            stats = {
                "total_files": 0,
                "situation_indexes": 0,
                "item_indexes": 0,
                "color_indexes": 0,
                "styling_indexes": 0
            }
            
            # 전체 파일 수
            pattern = f"{self.metadata_prefix}:*"
            keys = redis_service.keys(pattern)
            stats["total_files"] = len(keys)
            
            # 각 인덱스 타입별 개수
            index_types = ["situation", "item", "color", "styling"]
            for index_type in index_types:
                pattern = f"{self.index_prefix}:{index_type}:*"
                keys = redis_service.keys(pattern)
                stats[f"{index_type}_indexes"] = len(keys)
            
            return stats
            
        except Exception as e:
            print(f"❌ 인덱스 통계 조회 실패: {e}")
            return {}

# 전역 인스턴스 생성
fashion_index_service = FashionIndexService() 