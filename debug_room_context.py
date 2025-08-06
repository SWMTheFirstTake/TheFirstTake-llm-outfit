#!/usr/bin/env python3
"""
room_id 67의 컨텍스트 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.redis_service import redis_service
from services.s3_service import s3_service

def debug_room_context(room_id: int):
    """room_id의 컨텍스트 디버깅"""
    try:
        print(f"🔍 room_id {room_id} 컨텍스트 디버깅 시작...")
        
        # 최근 사용된 착장들 가져오기
        recent_outfits = redis_service.get_recent_used_outfits(room_id, limit=5)
        print(f"📊 최근 사용된 착장 수: {len(recent_outfits)}")
        
        if not recent_outfits:
            print("⚠️ 최근 사용된 착장이 없음 - 이것이 fallback의 원인!")
            return
        
        print("📋 최근 사용된 착장 목록:")
        for i, filename in enumerate(recent_outfits):
            print(f"   {i+1}. {filename}")
            
            # S3에서 착장 정보 가져오기
            try:
                json_content = s3_service.get_json_content(filename)
                if json_content:
                    situations = json_content.get('situations', [])
                    print(f"      상황: {situations}")
                else:
                    print(f"      ❌ JSON 내용을 가져올 수 없음")
            except Exception as e:
                print(f"      ❌ 착장 분석 실패: {e}")
        
        # Redis 키 확인
        room_key = f"recent_outfits:{room_id}"
        exists = redis_service.exists(room_key)
        print(f"📊 Redis 키 '{room_key}' 존재: {exists}")
        
        if exists:
            members = redis_service.lrange(room_key, 0, -1)
            print(f"📊 Redis 멤버 수: {len(members)}")
            print(f"📋 Redis 멤버들: {members}")
        
    except Exception as e:
        print(f"❌ 컨텍스트 디버깅 실패: {e}")

if __name__ == "__main__":
    debug_room_context(67) 