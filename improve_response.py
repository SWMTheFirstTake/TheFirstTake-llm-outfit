import json
import os
from typing import List, Dict

def improve_json_response_generation():
    """JSON 데이터를 더 잘 활용하는 응답 생성 개선"""
    
    # JSON 데이터 로드
    pipeline_dir = r"C:\fashion_summary"
    all_fashion_items = []
    all_outfit_combinations = []
    all_color_recommendations = []
    
    print("📚 JSON 데이터 통합 분석")
    
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            file_path = os.path.join(pipeline_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'fashion_data' in data:
                        fashion_data = data['fashion_data']
                        
                        if 'fashion_items' in fashion_data:
                            all_fashion_items.extend(fashion_data['fashion_items'])
                        
                        if 'outfit_combinations' in fashion_data:
                            all_outfit_combinations.extend(fashion_data['outfit_combinations'])
                        
                        if 'color_recommendations' in fashion_data:
                            all_color_recommendations.extend(fashion_data['color_recommendations'])
                            
            except Exception as e:
                print(f"⚠️ {filename} 읽기 실패: {e}")
    
    print(f"📊 통합 데이터:")
    print(f"   - 패션 아이템: {len(all_fashion_items)}개")
    print(f"   - 아웃핏 조합: {len(all_outfit_combinations)}개")
    print(f"   - 컬러 추천: {len(all_color_recommendations)}개")
    
    # 상황별 추천 생성
    scenarios = {
        "데이트": ["데이트", "소개팅", "카페", "연애"],
        "출근": ["출근", "면접", "직장", "비즈니스", "미팅"],
        "여름": ["여름", "휴가", "리조트", "시원한"],
        "겨울": ["겨울", "따뜻한", "보온"],
        "캐주얼": ["캐주얼", "데일리", "편한", "일상"]
    }
    
    print(f"\n🎯 상황별 추천 생성:")
    
    for scenario, keywords in scenarios.items():
        print(f"\n📌 {scenario} 상황:")
        
        # 관련 아웃핏 조합 찾기
        relevant_combos = []
        for combo in all_outfit_combinations:
            occasion = combo.get('occasion', '').lower()
            if any(keyword in occasion for keyword in keywords):
                relevant_combos.append(combo)
        
        if relevant_combos:
            print(f"   아웃핏 조합 {len(relevant_combos)}개:")
            for combo in relevant_combos[:3]:  # 상위 3개만
                items = combo.get('items', [])
                if isinstance(items, list):
                    items_str = ', '.join(items)
                else:
                    items_str = str(items)
                print(f"     - {combo.get('combination', '')}: {items_str}")
        
        # 관련 컬러 추천 찾기
        relevant_colors = []
        for color in all_color_recommendations:
            color_name = color.get('color', '').lower()
            description = color.get('description', '').lower()
            if any(keyword in color_name or keyword in description for keyword in keywords):
                relevant_colors.append(color)
        
        if relevant_colors:
            print(f"   컬러 추천 {len(relevant_colors)}개:")
            for color in relevant_colors[:2]:  # 상위 2개만
                print(f"     - {color.get('color', '')}: {color.get('description', '')}")

def generate_improved_response_template():
    """개선된 응답 템플릿 생성"""
    
    template = """
def generate_smart_response(user_input: str, expert_type: str, fashion_data: dict) -> str:
    \"\"\"스마트한 응답 생성\"\"\"
    
    # 1. 사용자 의도 분석
    user_intent = analyze_user_intent(user_input)
    
    # 2. 관련 데이터 찾기 (여러 개)
    relevant_items = find_relevant_items(user_input, fashion_data['fashion_items'])
    relevant_combos = find_relevant_combos(user_input, fashion_data['outfit_combinations'])
    relevant_colors = find_relevant_colors(user_input, fashion_data['color_recommendations'])
    
    # 3. 전문가별 특성 적용
    expert_style = get_expert_style(expert_type)
    
    # 4. 자연스러운 응답 생성
    response = create_natural_response(
        user_intent, relevant_items, relevant_combos, 
        relevant_colors, expert_style
    )
    
    return response
"""
    
    print("💡 개선된 응답 생성 템플릿:")
    print(template)

if __name__ == "__main__":
    improve_json_response_generation()
    print("\n" + "="*50)
    generate_improved_response_template() 