#!/usr/bin/env python3
"""
Redis 키를 직접 확인하는 간단한 스크립트
"""

import redis
import os

def test_redis_directly():
    """Redis에 직접 연결하여 키 확인"""
    try:
        # 환경변수에서 Redis 설정 가져오기
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        
        print(f"🔍 Redis 연결 설정: {redis_host}:{redis_port}, DB:{redis_db}")
        
        # Redis 연결
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        print("🔍 Redis 직접 연결 테스트...")
        
        # 모든 패션 인덱스 키 가져오기
        all_keys = r.keys("fashion_index:*")
        print(f"📊 전체 패션 인덱스 키 수: {len(all_keys)}")
        
        # 상황별 키들 확인
        situation_keys = r.keys("fashion_index:situation:*")
        print(f"📊 상황별 인덱스 키 수: {len(situation_keys)}")
        
        if situation_keys:
            print("📋 상황별 키 목록:")
            for key in sorted(situation_keys)[:10]:  # 처음 10개만
                print(f"   - {key}")
        
        # "소개팅" 관련 키 확인
        소개팅_keys = r.keys("*소개팅*")
        print(f"📊 '소개팅' 관련 키 수: {len(소개팅_keys)}")
        
        if 소개팅_keys:
            print("📋 '소개팅' 관련 키 목록:")
            for key in 소개팅_keys:
                print(f"   - {key}")
        
        # 특정 키의 멤버 확인
        소개팅_situation_key = "fashion_index:situation:소개팅"
        if r.exists(소개팅_situation_key):
            members = r.smembers(소개팅_situation_key)
            print(f"📊 '{소개팅_situation_key}' 멤버 수: {len(members)}")
            if members:
                print("📋 멤버 목록 (처음 5개):")
                for member in list(members)[:5]:
                    print(f"   - {member}")
        else:
            print(f"❌ '{소개팅_situation_key}' 키가 존재하지 않음")
        
        # 다른 가능한 키들 확인
        possible_keys = [
            "fashion_index:situation:소개팅",
            "fashion_index:situation:소개팅",
            "fashion_index:situation:소개팅",
            "fashion_index:situation:소개팅"
        ]
        
        print("🔍 가능한 키들 확인:")
        for key in possible_keys:
            exists = r.exists(key)
            print(f"   - {key}: {'존재' if exists else '없음'}")
            if exists:
                members = r.smembers(key)
                print(f"     멤버 수: {len(members)}")
        
    except Exception as e:
        print(f"❌ Redis 연결 실패: {e}")

if __name__ == "__main__":
    test_redis_directly() 