import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any

class GradualLoadTester:
    def __init__(self, base_url: str = "https://the-second-take.com"):
        self.base_url = base_url
        self.endpoint = "/api/chat/rooms/messages/stream"
        self.user_input = "소개팅을 가야 하는 상황이야"
        
    async def single_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """단일 요청을 보내고 결과를 반환합니다."""
        url = f"{self.base_url}{self.endpoint}"
        params = {"user_input": self.user_input}
        
        start_time = time.time()
        events_received = []
        total_content = ""
        
        try:
            async with session.get(url, params=params) as response:
                status_code = response.status
                
                if status_code == 200:
                    # SSE 스트림 읽기
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_content = line_str[6:]
                                total_content += data_content + "\n"
                                
                                try:
                                    import json
                                    parsed_data = json.loads(data_content)
                                    events_received.append({
                                        "type": parsed_data.get("data", {}).get("type", "unknown"),
                                        "message": parsed_data.get("message", ""),
                                        "agent": parsed_data.get("data", {}).get("agent_name", "")
                                    })
                                except:
                                    events_received.append({"raw": data_content})
                    
                    response_time = time.time() - start_time
                    
                    return {
                        "request_id": request_id,
                        "status_code": status_code,
                        "response_time": response_time,
                        "content_length": len(total_content),
                        "success": True,
                        "error": None,
                        "events_received": len(events_received),
                        "event_types": [event.get("type", "raw") for event in events_received],
                        "response_content": total_content[:500] if total_content else None
                    }
                else:
                    content = await response.text()
                    response_time = time.time() - start_time
                    
                    return {
                        "request_id": request_id,
                        "status_code": status_code,
                        "response_time": response_time,
                        "content_length": len(content),
                        "success": False,
                        "error": f"HTTP {status_code}",
                        "events_received": 0,
                        "event_types": [],
                        "response_content": content[:500] if content else None
                    }
                    
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "request_id": request_id,
                "status_code": None,
                "response_time": response_time,
                "content_length": 0,
                "success": False,
                "error": str(e),
                "events_received": 0,
                "event_types": [],
                "response_content": None
            }
    
    async def test_concurrent_requests(self, num_requests: int) -> List[Dict[str, Any]]:
        """동시 요청 테스트"""
        print(f"🔄 동시 {num_requests}개 요청 테스트 시작")
        
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=num_requests + 5)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            tasks = [self.single_request(session, i+1) for i in range(num_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "request_id": i+1,
                    "status_code": None,
                    "response_time": 0,
                    "content_length": 0,
                    "success": False,
                    "error": str(result),
                    "events_received": 0,
                    "event_types": [],
                    "response_content": None
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def print_results(self, results: List[Dict[str, Any]], test_name: str):
        """결과를 출력합니다."""
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        print(f"\n📊 {test_name} 결과:")
        print(f"✅ 성공: {len(successful_requests)}/{len(results)}")
        print(f"❌ 실패: {len(failed_requests)}/{len(results)}")
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            print(f"⏱️  평균 응답 시간: {avg_response_time:.3f}초")
            print(f"⚡ 최소 응답 시간: {min_response_time:.3f}초")
            print(f"🐌 최대 응답 시간: {max_response_time:.3f}초")
        
        if failed_requests:
            print(f"❌ 실패한 요청:")
            for failed in failed_requests[:3]:
                error_msg = failed.get('error', 'Unknown error')
                print(f"  - 요청 #{failed['request_id']}: {error_msg}")

async def main():
    """점진적 부하 테스트"""
    print("🚀 점진적 부하 테스트 시작")
    print("동시 연결 수를 점진적으로 늘려가며 서버의 한계를 찾습니다.")
    print("-" * 60)
    
    tester = GradualLoadTester()
    
    # 테스트할 동시 연결 수들
    concurrent_counts = [1, 2, 3, 5, 10]
    
    all_results = {}
    
    for count in concurrent_counts:
        print(f"\n{'='*60}")
        print(f"🔍 동시 {count}개 요청 테스트")
        
        start_time = time.time()
        results = await tester.test_concurrent_requests(count)
        total_time = time.time() - start_time
        
        tester.print_results(results, f"동시 {count}개")
        print(f"⏰ 총 테스트 시간: {total_time:.3f}초")
        
        # 성공률 계산
        success_rate = len([r for r in results if r["success"]]) / len(results) * 100
        print(f"📈 성공률: {success_rate:.1f}%")
        
        all_results[f"concurrent_{count}"] = {
            "results": results,
            "total_time": total_time,
            "success_rate": success_rate
        }
        
        # 다음 테스트 전에 잠시 대기
        if count < concurrent_counts[-1]:
            print("⏳ 다음 테스트를 위해 5초 대기...")
            await asyncio.sleep(5)
    
    # 결과 저장
    with open("gradual_load_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_config": {
                "url": f"{tester.base_url}{tester.endpoint}",
                "user_input": tester.user_input,
                "concurrent_counts": concurrent_counts
            },
            "results": all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과가 gradual_load_test_results.json 파일에 저장되었습니다.")
    
    # 권장사항 출력
    print(f"\n📋 권장사항:")
    for count in concurrent_counts:
        result = all_results[f"concurrent_{count}"]
        success_rate = result["success_rate"]
        if success_rate >= 80:
            print(f"✅ 동시 {count}개 연결: 안전 (성공률 {success_rate:.1f}%)")
        elif success_rate >= 50:
            print(f"⚠️  동시 {count}개 연결: 주의 필요 (성공률 {success_rate:.1f}%)")
        else:
            print(f"❌ 동시 {count}개 연결: 위험 (성공률 {success_rate:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())
