import json
import os

def test_improved_response():
    """개선된 응답 테스트"""
    print("개선된 응답 테스트")
    
    # 데이터 로드
    reference_data = {
        "fashion_items": [],
        "outfit_combinations": [],
        "styling_tips": [],
        "color_recommendations": [],
        "seasonal_advice": []
    }
    
    pipeline_dir = r"C:\fashion_summary"
    
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
                continue
    
    # 소개팅 입력 테스트
    test_input = "소개팅"
    user_keywords = test_input.lower().split()
    
    # 키워드 확장
    expanded_keywords = user_keywords.copy()
    for keyword in user_keywords:
        if keyword == '소개팅':
            expanded_keywords.extend(['소개팅', '데이트', '미팅'])
    
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
    
    # 최적 조합 선택
    if actual_combos:
        combo = actual_combos[0]
        if len(actual_combos) > 1:
            # 1순위: occasion이 정확히 매칭되는 것
            for c in actual_combos:
                if c.get('occasion') and any(keyword in c['occasion'].lower() for keyword in ['소개팅']):
                    combo = c
                    break
        
        # 응답 생성 (개선된 버전)
        response_parts = []
        
        # 기본 응답
        if isinstance(combo['items'], list):
            items_str = ', '.join(combo['items'])
        else:
            items_str = str(combo['items'])
        
        response_parts.append(f"체형을 보니 {combo['combination']}이 핏감과 실루엣에 완벽해! 핏감 중심의 깔끔한 스타일이야!")
        response_parts.append(f"구체적으로는 {items_str} 조합을 추천해!")
        
        if combo.get('occasion'):
            response_parts.append(f"이 조합은 {combo['occasion']}에 특히 어울려!")
        
        # 첫 번째 아이템의 스타일링 팁만 추가
        if isinstance(combo['items'], list) and combo['items']:
            first_item_name = combo['items'][0]
            for item in reference_data['fashion_items']:
                if (first_item_name.lower() in item['item'].lower() or 
                    item['item'].lower() in first_item_name.lower()):
                    if item.get('styling_tips'):
                        response_parts.append(f"💡 {item['item']} 스타일링: {item['styling_tips']}")
                    break
        
        final_response = " ".join(response_parts)
        print(f"\n🎉 개선된 응답:")
        print(f"{final_response}")
        
        # 이전 응답과 비교
        print(f"\n📊 응답 길이: {len(final_response)}자")
        print(f"📊 응답 구성 요소: {len(response_parts)}개")
        
    else:
        print("매칭된 조합이 없습니다.")

if __name__ == "__main__":
    test_improved_response() 