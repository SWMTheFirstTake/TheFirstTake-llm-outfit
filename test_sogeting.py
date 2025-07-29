import json
import os

def test_sogeting_response():
    """소개팅 입력에 대한 응답 테스트"""
    print("소개팅 입력 테스트")
    
    # 서비스와 동일한 데이터 로딩
    reference_data = {
        "fashion_items": [],
        "outfit_combinations": [],
        "styling_tips": [],
        "color_recommendations": [],
        "seasonal_advice": []
    }
    
    pipeline_dir = r"C:\fashion_summary"
    
    # JSON 데이터 로드
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            file_path = os.path.join(pipeline_dir, filename)
            
            try:
                encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
                data = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            data = json.load(f)
                            break
                    except:
                        continue
                
                if data and 'fashion_data' in data:
                    fashion_data = data['fashion_data']
                    
                    if 'fashion_items' in fashion_data:
                        reference_data['fashion_items'].extend(fashion_data['fashion_items'])
                    
                    if 'outfit_combinations' in fashion_data:
                        reference_data['outfit_combinations'].extend(fashion_data['outfit_combinations'])
                    
                    if 'color_recommendations' in fashion_data:
                        reference_data['color_recommendations'].extend(fashion_data['color_recommendations'])
                    
                    if 'styling_tips' in fashion_data:
                        reference_data['styling_tips'].extend(fashion_data['styling_tips'])
                        
            except Exception as e:
                print(f"Error with {filename}: {e}")
    
    print(f"로드된 데이터:")
    print(f"  아웃핏 조합: {len(reference_data['outfit_combinations'])}개")
    
    # 소개팅 입력 테스트
    test_input = "소개팅"
    print(f"\n--- 테스트 입력: '{test_input}' ---")
    
    # 키워드 확장
    user_keywords = test_input.lower().split()
    expanded_keywords = user_keywords.copy()
    for keyword in user_keywords:
        if keyword == '소개팅':
            expanded_keywords.extend(['소개팅', '데이트', '미팅'])
    
    print(f"원본 키워드: {user_keywords}")
    print(f"확장된 키워드: {expanded_keywords}")
    
    # 매칭된 조합 찾기
    actual_combos = []
    
    for combo in reference_data['outfit_combinations']:
        items_list = combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]
        occasion_str = ""
        if combo['occasion'] is not None:
            if isinstance(combo['occasion'], str):
                occasion_str = combo['occasion'].lower()
            else:
                occasion_str = str(combo['occasion']).lower()
        
        combination_match = any(keyword in combo['combination'].lower() for keyword in expanded_keywords)
        items_match = any(any(keyword in item.lower() for keyword in expanded_keywords) for item in items_list)
        occasion_match = any(keyword in occasion_str for keyword in expanded_keywords) if occasion_str else False
        
        if combination_match or items_match or occasion_match:
            actual_combos.append(combo)
            print(f"✅ 매칭 발견: '{combo['combination']}' (occasion: '{combo['occasion']}')")
    
    print(f"\n총 {len(actual_combos)}개 조합 매칭됨")
    
    # 최적 조합 선택
    if actual_combos:
        combo = actual_combos[0]
        if len(actual_combos) > 1:
            print(f"🔍 {len(actual_combos)}개 조합 중에서 최적 선택 중...")
            
            # 1순위: occasion이 정확히 매칭되는 것
            for c in actual_combos:
                if c.get('occasion') and any(keyword in c['occasion'].lower() for keyword in ['소개팅']):
                    combo = c
                    print(f"✅ 소개팅 occasion 매칭으로 선택: '{c['combination']}' (occasion: '{c['occasion']}')")
                    break
        
        # 응답 생성
        if isinstance(combo['items'], list):
            items_str = ', '.join(combo['items'])
        else:
            items_str = str(combo['items'])
        
        response = f"체형을 보니 {combo['combination']}이 핏감과 실루엣에 완벽해! 핏감 중심의 깔끔한 스타일이야! 구체적으로는 {items_str} 조합을 추천해!"
        
        if combo.get('occasion'):
            response += f" 이 조합은 {combo['occasion']}에 특히 어울려!"
        
        print(f"\n🎉 최종 응답:")
        print(f"{response}")
    else:
        print("매칭된 조합이 없습니다.")

if __name__ == "__main__":
    test_sogeting_response() 