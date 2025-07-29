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

# 소개팅 조합들 확인
sogeting_combos = []
for combo in data['outfit_combinations']:
    occasion = str(combo.get('occasion', '')).lower()
    if '소개팅' in occasion or '데이트' in occasion:
        sogeting_combos.append(combo)

print(f'소개팅/데이트 관련 조합 {len(sogeting_combos)}개 발견:')
print('=' * 50)

for i, combo in enumerate(sogeting_combos, 1):
    items_str = ', '.join(combo['items']) if isinstance(combo['items'], list) else str(combo['items'])
    print(f'{i}. {combo["combination"]}')
    print(f'   아이템: {items_str}')
    print(f'   상황: {combo.get("occasion", "N/A")}')
    print()

# 스트라이프 셔츠가 포함된 조합들 확인
striped_combos = []
for combo in data['outfit_combinations']:
    items = combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]
    if any('스트라이프' in item or '셔츠' in item for item in items):
        striped_combos.append(combo)

print(f'\n스트라이프 셔츠 관련 조합 {len(striped_combos)}개:')
print('=' * 50)

for i, combo in enumerate(striped_combos, 1):
    items_str = ', '.join(combo['items']) if isinstance(combo['items'], list) else str(combo['items'])
    print(f'{i}. {combo["combination"]}')
    print(f'   아이템: {items_str}')
    print(f'   상황: {combo.get("occasion", "N/A")}')
    print() 