import asyncio
import aiohttp
import time
import json

async def test_single_request():
    """단일 요청으로 API 테스트"""
    url = "https://the-second-take.com/api/chat/rooms/messages/stream"
    params = {"user_input": "소개팅을 가야 하는 상황이야"}
    
    print(f"🔍 단일 요청 테스트 시작")
    print(f"URL: {url}")
    print(f"파라미터: {params}")
    print("-" * 50)
    
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        start_time = time.time()
        
        try:
            async with session.get(url, params=params) as response:
                print(f"📡 응답 상태: {response.status}")
                print(f"📋 응답 헤더:")
                for key, value in response.headers.items():
                    print(f"  {key}: {value}")
                print()
                
                if response.status == 200:
                    print("📺 SSE 스트림 데이터:")
                    event_count = 0
                    
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            event_count += 1
                            
                            if line_str.startswith('event: '):
                                print(f"🎯 이벤트 타입: {line_str[7:]}")
                            elif line_str.startswith('data: '):
                                data_content = line_str[6:]
                                print(f"📦 데이터: {data_content[:200]}...")
                                
                                try:
                                    parsed = json.loads(data_content)
                                    if parsed.get("status") == "success":
                                        data = parsed.get("data", {})
                                        print(f"   ✅ 성공 - 타입: {data.get('type')}, 메시지: {data.get('message', '')[:50]}...")
                                    else:
                                        print(f"   ❌ 실패 - {parsed.get('message')}")
                                except json.JSONDecodeError:
                                    print(f"   ⚠️  JSON 파싱 실패")
                            
                            if event_count > 20:  # 너무 많은 이벤트 방지
                                print("   ... (이벤트가 많아서 일부만 표시)")
                                break
                    
                    response_time = time.time() - start_time
                    print(f"\n⏱️  총 응답 시간: {response_time:.3f}초")
                    print(f"📊 수신된 이벤트 수: {event_count}개")
                    
                else:
                    # 에러 응답
                    content = await response.text()
                    response_time = time.time() - start_time
                    print(f"❌ 에러 응답 ({response.status}):")
                    print(content)
                    print(f"\n⏱️  응답 시간: {response_time:.3f}초")
                    
        except Exception as e:
            response_time = time.time() - start_time
            print(f"💥 예외 발생: {str(e)}")
            print(f"⏱️  시간: {response_time:.3f}초")

if __name__ == "__main__":
    asyncio.run(test_single_request())
