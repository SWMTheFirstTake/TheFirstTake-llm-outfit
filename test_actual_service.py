import json
import os

def test_actual_response():
    """실제 응답 생성 테스트"""
    print("Testing actual response generation")
    
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
    
    print(f"Loaded data:")
    print(f"  Fashion items: {len(reference_data['fashion_items'])}")
    print(f"  Outfit combinations: {len(reference_data['outfit_combinations'])}")
    print(f"  Color recommendations: {len(reference_data['color_recommendations'])}")
    print(f"  Styling tips: {len(reference_data['styling_tips'])}")
    
    # 응답 생성 테스트
    test_inputs = ["데이트룩 추천해줘", "출근복 추천해줘", "여름 옷 추천해줘"]
    
    for test_input in test_inputs:
        print(f"\n--- Testing: {test_input} ---")
        
        # 키워드 매칭
        user_keywords = test_input.lower().split()
        print(f"Keywords: {user_keywords}")
        
        # 매칭된 데이터 찾기
        actual_items = []
        actual_combos = []
        actual_colors = []
        
        # 패션 아이템 매칭
        for item in reference_data['fashion_items']:
            if any(keyword in item['item'].lower() for keyword in user_keywords):
                actual_items.append(item)
        
        # 아웃핏 조합 매칭
        for combo in reference_data['outfit_combinations']:
            items_list = combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]
            occasion_str = ""
            if combo['occasion'] is not None:
                if isinstance(combo['occasion'], str):
                    occasion_str = combo['occasion'].lower()
                else:
                    occasion_str = str(combo['occasion']).lower()
            
            combination_match = any(keyword in combo['combination'].lower() for keyword in user_keywords)
            items_match = any(any(keyword in item.lower() for keyword in user_keywords) for item in items_list)
            occasion_match = any(keyword in occasion_str for keyword in user_keywords) if occasion_str else False
            
            if combination_match or items_match or occasion_match:
                actual_combos.append(combo)
        
        # 컬러 추천 매칭
        for color in reference_data['color_recommendations']:
            if any(keyword in color['color'].lower() for keyword in user_keywords):
                actual_colors.append(color)
        
        print(f"Matched: items={len(actual_items)}, combos={len(actual_combos)}, colors={len(actual_colors)}")
        
        # 응답 생성
        if actual_combos:
            combo = actual_combos[0]
            if isinstance(combo['items'], list):
                items_str = ', '.join(combo['items'])
            else:
                items_str = str(combo['items'])
            
            response = f"체형을 보니 {combo['combination']}이 핏감과 실루엣에 완벽해! 핏감 중심의 깔끔한 스타일이야! 구체적으로는 {items_str} 조합을 추천해!"
            
            if combo.get('occasion'):
                response += f" 이 조합은 {combo['occasion']}에 특히 어울려!"
            
            print(f"Response: {response}")
        else:
            print("No matching combinations found")

if __name__ == "__main__":
    test_actual_response() 