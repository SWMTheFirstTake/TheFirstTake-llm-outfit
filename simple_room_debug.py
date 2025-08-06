#!/usr/bin/env python3
"""
room_id 67의 Redis 상태 확인
"""

import redis
import os

def debug_room_redis(room_id: int):
    """room_id의 Redis 상태 확인"""
    try:
        # Redis 연결
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        print(f"🔍 room_id {room_id} Redis 상태 확인...")
        
        # 최근 착장 키 확인 (올바른 형식)
        room_key = f"{room_id}:recent_outfits"
        exists = r.exists(room_key)
        print(f"📊 Redis 키 '{room_key}' 존재: {exists}")
        
        if exists:
            members = r.lrange(room_key, 0, -1)
            print(f"📊 Redis 멤버 수: {len(members)}")
            print(f"📋 Redis 멤버들: {members}")
        else:
            print("⚠️ 최근 착장 히스토리가 없음 - 이것이 fallback의 원인!")
        
        # 다른 room_id들도 확인
        print("\n🔍 다른 room_id들 확인:")
        all_room_keys = r.keys("*:recent_outfits")
        for key in sorted(all_room_keys):
            members = r.lrange(key, 0, -1)
            print(f"   {key}: {len(members)}개 멤버")
        
    except Exception as e:
        print(f"❌ Redis 확인 실패: {e}")

if __name__ == "__main__":
    debug_room_redis(67) 