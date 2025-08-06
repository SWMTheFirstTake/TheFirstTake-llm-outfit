import redis
import json
import os

def check_redis_metadata():
    """Redis에 저장된 패션 메타데이터 확인"""
    
    # Redis 연결
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True
    )
    
    try:
        # 메타데이터 키들 조회
        metadata_keys = redis_client.keys("fashion_metadata:*")
        print(f"📊 총 메타데이터 개수: {len(metadata_keys)}개")
        
        if not metadata_keys:
            print("❌ 메타데이터가 없습니다!")
            return
        
        # 첫 번째 메타데이터 샘플 확인
        sample_key = metadata_keys[0]
        print(f"\n🔍 샘플 메타데이터 확인: {sample_key}")
        
        metadata = redis_client.get(sample_key)
        if metadata:
            data = json.loads(metadata)
            print("✅ 메타데이터 구조:")
            print(f"   - 파일명: {data.get('filename', 'N/A')}")
            print(f"   - S3 URL: {data.get('s3_url', 'N/A')}")
            print(f"   - 상황: {data.get('situations', [])}")
            print(f"   - 아이템: {list(data.get('items', {}).keys())}")
            print(f"   - 타임스탬프: {data.get('timestamp', 'N/A')}")
        
        # 인덱스 키들도 확인
        print(f"\n🔍 인덱스 키들 확인:")
        
        # 상황별 인덱스
        situation_keys = redis_client.keys("fashion_index:situation:*")
        print(f"   - 상황별 인덱스: {len(situation_keys)}개")
        for key in situation_keys[:5]:  # 상위 5개만
            members = redis_client.smembers(key)
            print(f"     {key}: {len(members)}개 파일")
        
        # 아이템별 인덱스
        item_keys = redis_client.keys("fashion_index:item:*")
        print(f"   - 아이템별 인덱스: {len(item_keys)}개")
        for key in item_keys[:5]:  # 상위 5개만
            members = redis_client.smembers(key)
            print(f"     {key}: {len(members)}개 파일")
        
        # 색상별 인덱스
        color_keys = redis_client.keys("fashion_index:color:*")
        print(f"   - 색상별 인덱스: {len(color_keys)}개")
        for key in color_keys[:5]:  # 상위 5개만
            members = redis_client.smembers(key)
            print(f"     {key}: {len(members)}개 파일")
        
        # 검색 테스트
        print(f"\n🔍 검색 테스트:")
        
        # "일상" 상황 검색
        daily_key = "fashion_index:situation:일상"
        daily_files = redis_client.smembers(daily_key)
        print(f"   - '일상' 상황: {len(daily_files)}개 파일")
        
        # "니트" 아이템 검색
        knit_key = "fashion_index:item:니트"
        knit_files = redis_client.smembers(knit_key)
        print(f"   - '니트' 아이템: {len(knit_files)}개 파일")
        
        # "블랙" 색상 검색
        black_key = "fashion_index:color:블랙"
        black_files = redis_client.smembers(black_key)
        print(f"   - '블랙' 색상: {len(black_files)}개 파일")
        
        print(f"\n✅ 인덱스 시스템이 정상적으로 작동하고 있습니다!")
        
    except Exception as e:
        print(f"❌ Redis 확인 중 에러: {e}")

if __name__ == "__main__":
    check_redis_metadata() 