#!/usr/bin/env python3
"""
Redis에 저장된 패션 인덱스 키들을 확인하는 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.redis_service import redis_service

def test_redis_keys():
    """Redis에 저장된 패션 인덱스 키들을 확인"""
    try:
        print("🔍 Redis 패션 인덱스 키 확인 중...")
        
        # 모든 패션 인덱스 키 가져오기
        all_keys = redis_service.keys("fashion_index:*")
        print(f"📊 전체 패션 인덱스 키 수: {len(all_keys)}")
        
        # 상황별 키들 확인
        situation_keys = redis_service.keys("fashion_index:situation:*")
        print(f"📊 상황별 인덱스 키 수: {len(situation_keys)}")
        
        if situation_keys:
            print("📋 상황별 키 목록:")
            for key in sorted(situation_keys)[:10]:  # 처음 10개만
                print(f"   - {key}")
        
        # "소개팅" 관련 키 확인
        소개팅_keys = redis_service.keys("*소개팅*")
        print(f"📊 '소개팅' 관련 키 수: {len(소개팅_keys)}")
        
        if 소개팅_keys:
            print("📋 '소개팅' 관련 키 목록:")
            for key in 소개팅_keys:
                print(f"   - {key}")
        
        # 특정 키의 멤버 확인
        소개팅_situation_key = "fashion_index:situation:소개팅"
        if redis_service.exists(소개팅_situation_key):
            members = redis_service.smembers(소개팅_situation_key)
            print(f"📊 '{소개팅_situation_key}' 멤버 수: {len(members)}")
            if members:
                print("📋 멤버 목록 (처음 5개):")
                for member in list(members)[:5]:
                    print(f"   - {member}")
        else:
            print(f"❌ '{소개팅_situation_key}' 키가 존재하지 않음")
        
        # 대소문자 변형 확인
        소개팅_lower_key = "fashion_index:situation:소개팅"
        소개팅_upper_key = "fashion_index:situation:소개팅"
        
        print(f"📊 소문자 키 존재: {redis_service.exists(소개팅_lower_key)}")
        print(f"📊 원본 키 존재: {redis_service.exists(소개팅_upper_key)}")
        
    except Exception as e:
        print(f"❌ Redis 키 확인 실패: {e}")

if __name__ == "__main__":
    test_redis_keys() 