import json
import os

# 데이터 로드
data = {'outfit_combinations': []}
pipeline_dir = r'C:\fashion_summary'

for f in os.listdir(pipeline_dir):
    if f.endswith('.json') and f.startswith('fashion_extract_'):
        try:
            with open(os.path.join(pipeline_dir, f), 'r', encoding='utf-8') as file:
                json_data = json.load(file)
                if 'fashion_data' in json_data and 'outfit_combinations' in json_data['fashion_data']:
                    data['outfit_combinations'].extend(json_data['fashion_data']['outfit_combinations'])
        except:
            continue

# 소개팅 조합 찾기
sogeting = [c for c in data['outfit_combinations'] if '소개팅' in str(c.get('occasion', '')).lower()]

print(f'소개팅 조합 {len(sogeting)}개:')
for c in sogeting[:5]:
    print(f'- {c["combination"]}: {c["occasion"]}')

# 첫 번째 소개팅 조합으로 응답 생성
if sogeting:
    combo = sogeting[0]
    items_str = ', '.join(combo['items']) if isinstance(combo['items'], list) else str(combo['items'])
    response = f"체형을 보니 {combo['combination']}이 핏감과 실루엣에 완벽해! 구체적으로는 {items_str} 조합을 추천해!"
    if combo.get('occasion'):
        response += f" 이 조합은 {combo['occasion']}에 특히 어울려!"
    print(f"\n응답: {response}")
else:
    print("소개팅 조합을 찾을 수 없습니다.") 