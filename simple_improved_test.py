import json
import os

# 데이터 로드
data = {'outfit_combinations': [], 'fashion_items': []}
pipeline_dir = r'C:\fashion_summary'

for f in os.listdir(pipeline_dir):
    if f.endswith('.json') and f.startswith('fashion_extract_'):
        try:
            with open(os.path.join(pipeline_dir, f), 'r', encoding='utf-8') as file:
                json_data = json.load(file)
                if 'fashion_data' in json_data:
                    if 'outfit_combinations' in json_data['fashion_data']:
                        data['outfit_combinations'].extend(json_data['fashion_data']['outfit_combinations'])
                    if 'fashion_items' in json_data['fashion_data']:
                        data['fashion_items'].extend(json_data['fashion_data']['fashion_items'])
        except:
            continue

# 소개팅 조합 찾기
sogeting = [c for c in data['outfit_combinations'] if '소개팅' in str(c.get('occasion', '')).lower()]

print(f'소개팅 조합 {len(sogeting)}개 발견')

if sogeting:
    combo = sogeting[0]  # 첫 번째 소개팅 조합
    items_str = ', '.join(combo['items']) if isinstance(combo['items'], list) else str(combo['items'])
    
    # 개선된 응답 생성
    response_parts = []
    response_parts.append(f"체형을 보니 {combo['combination']}이 핏감과 실루엣에 완벽해! 핏감 중심의 깔끔한 스타일이야!")
    response_parts.append(f"구체적으로는 {items_str} 조합을 추천해!")
    
    if combo.get('occasion'):
        response_parts.append(f"이 조합은 {combo['occasion']}에 특히 어울려!")
    
    # 첫 번째 아이템의 스타일링 팁만 추가
    if isinstance(combo['items'], list) and combo['items']:
        first_item_name = combo['items'][0]
        for item in data['fashion_items']:
            if (first_item_name.lower() in item['item'].lower() or 
                item['item'].lower() in first_item_name.lower()):
                if item.get('styling_tips'):
                    response_parts.append(f"💡 {item['item']} 스타일링: {item['styling_tips']}")
                break
    
    final_response = " ".join(response_parts)
    print(f"\n개선된 응답:")
    print(f"{final_response}")
    
    print(f"\n응답 길이: {len(final_response)}자")
    print(f"구성 요소: {len(response_parts)}개")
else:
    print("소개팅 조합을 찾을 수 없습니다.") 