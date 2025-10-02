import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any

class LoadTester:
    def __init__(self, base_url: str = "https://the-first-take.com"):
        self.base_url = base_url
        self.endpoint = "/api/chat/rooms/messages/stream"
        self.user_input = "소개팅을 가야 하는 상황이야"
        self.num_requests = 40
        
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
                                data_content = line_str[6:]  # 'data: ' 제거
                                total_content += data_content + "\n"
                                
                                try:
                                    # JSON 파싱 시도
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
                    # 에러 응답 처리
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
    
    async def single_request_with_new_session(self, request_id: int) -> Dict[str, Any]:
        """새로운 세션으로 단일 요청을 보내고 결과를 반환합니다."""
        # 매번 새로운 세션과 커넥터 생성
        timeout = aiohttp.ClientTimeout(total=1200)
        connector = aiohttp.TCPConnector(
            limit=10,  # 각 세션당 연결 수 제한
            limit_per_host=5,  # 호스트당 연결 수 제한
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        # 헤더 설정
        headers = {
            'User-Agent': 'LoadTester/1.0',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache'
        }
        
        async with aiohttp.ClientSession(
            timeout=timeout, 
            connector=connector,
            headers=headers,
            cookie_jar=aiohttp.DummyCookieJar()  # 쿠키 저장 안함
        ) as session:
            return await self.single_request(session, request_id)

    async def run_load_test(self, concurrent: bool = False) -> List[Dict[str, Any]]:
        """부하테스트를 실행합니다."""
        mode = "동시" if concurrent else "순차"
        print(f"부하테스트 시작: {self.num_requests}개의 요청을 {mode}로 {self.base_url}{self.endpoint}로 전송")
        print(f"사용자 입력: '{self.user_input}'")
        print("-" * 50)
        
        if concurrent:
            # 모든 요청을 동시에 시작 (각각 새로운 세션 사용)
            tasks = [self.single_request_with_new_session(i+1) for i in range(self.num_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 순차적으로 실행 (각 요청 사이에 1초 지연)
            results = []
            for i in range(self.num_requests):
                print(f"요청 #{i+1} 시작...")
                result = await self.single_request_with_new_session(i+1)
                results.append(result)
                if i < self.num_requests - 1:  # 마지막 요청이 아니면 지연
                    await asyncio.sleep(1)
        
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
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def print_results(self, results: List[Dict[str, Any]]):
        """결과를 출력합니다."""
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        # 성공률 계산
        success_rate = (len(successful_requests) / self.num_requests) * 100
        
        print(f"\n📊 전체 결과 요약:")
        print(f"  총 요청 수: {self.num_requests}개")
        print(f"  성공: {len(successful_requests)}개 ({success_rate:.1f}%)")
        print(f"  실패: {len(failed_requests)}개 ({100-success_rate:.1f}%)")
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            print(f"\n✅ 성공한 요청 상세:")
            print(f"  ⏱️  평균 응답 시간: {avg_response_time:.3f}초")
            print(f"  ⚡ 최소 응답 시간: {min_response_time:.3f}초")
            print(f"  🐌 최대 응답 시간: {max_response_time:.3f}초")
        
        if failed_requests:
            print(f"\n❌ 실패한 요청 분석:")
            
            # 에러 타입별 분류
            error_types = {}
            for failed in failed_requests:
                error_msg = failed.get('error', 'Unknown error')
                if 'TransferEncodingError' in error_msg:
                    error_types['TransferEncodingError'] = error_types.get('TransferEncodingError', 0) + 1
                elif 'timeout' in error_msg.lower():
                    error_types['Timeout'] = error_types.get('Timeout', 0) + 1
                elif 'connection' in error_msg.lower():
                    error_types['Connection Error'] = error_types.get('Connection Error', 0) + 1
                else:
                    error_types['Other'] = error_types.get('Other', 0) + 1
            
            print(f"  에러 타입별 분포:")
            for error_type, count in error_types.items():
                print(f"    - {error_type}: {count}개")
            
            # 실패 시간 분석
            failed_times = [r["response_time"] for r in failed_requests if r["response_time"] > 0]
            if failed_times:
                avg_failed_time = sum(failed_times) / len(failed_times)
                print(f"  평균 실패 시간: {avg_failed_time:.3f}초")
            
            print(f"\n  상세 실패 내역 (처음 5개):")
            for failed in failed_requests[:5]:
                error_msg = failed.get('error', 'Unknown error')
                status_code = failed.get('status_code', 'N/A')
                
                print(f"    - 요청 #{failed['request_id']}: 상태코드 {status_code}")
                print(f"      에러: {error_msg}")
                print(f"      실패 시간: {failed['response_time']:.3f}초")
                print()
        
        # 상태 코드별 통계
        status_counts = {}
        for result in results:
            status = result.get("status_code")
            if status:
                status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            print(f"\n📈 상태 코드별 통계:")
            for status, count in sorted(status_counts.items()):
                print(f"  - {status}: {count}개")
        
        # 개별 요청 결과 (간단히)
        print(f"\n📋 개별 요청 결과:")
        for result in results[:10]:  # 처음 10개만 표시
            status = "✅" if result["success"] else "❌"
            events_count = result.get("events_received", 0)
            event_types = result.get("event_types", [])
            event_summary = f" (이벤트 {events_count}개: {', '.join(set(event_types))})" if events_count > 0 else ""
            print(f"  {status} 요청 #{result['request_id']}: {result['response_time']:.3f}초{event_summary}")
        
        if len(results) > 10:
            print(f"  ... ({len(results) - 10}개 더)")
        
        # SSE 이벤트 타입 통계
        all_event_types = []
        for result in results:
            all_event_types.extend(result.get("event_types", []))
        
        if all_event_types:
            from collections import Counter
            event_counts = Counter(all_event_types)
            print(f"\n📊 수신된 이벤트 타입 통계:")
            for event_type, count in event_counts.most_common():
                print(f"  - {event_type}: {count}회")

async def main():
    """메인 함수"""
    print("🚀 동시 부하테스트 시작")
    
    load_tester = LoadTester()
    
    # 동시 요청 테스트만 실행
    print("\n📤 동시 요청 테스트")
    start_time = time.time()
    concurrent_results = await load_tester.run_load_test(concurrent=True)
    concurrent_time = time.time() - start_time
    
    load_tester.print_results(concurrent_results)
    print(f"\n⏰ 동시 테스트 총 시간: {concurrent_time:.3f}초")
    print(f"🔄 동시 테스트 RPS: {load_tester.num_requests / concurrent_time:.2f}")
    
    # 결과를 JSON 파일로 저장
    with open("concurrent_load_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_config": {
                "url": f"{load_tester.base_url}{load_tester.endpoint}",
                "user_input": load_tester.user_input,
                "num_requests": load_tester.num_requests
            },
            "concurrent_test": {
                "results": concurrent_results,
                "total_time": concurrent_time
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과가 concurrent_load_test_results.json 파일에 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())
