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

for combo in data['outfit_combinations']:
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

print(f'매칭된 조합 {len(actual_combos)}개 발견')

# 개선된 선택 로직
if actual_combos:
    combo = actual_combos[0]
    if len(actual_combos) > 1:
        print(f"🔍 {len(actual_combos)}개 조합 중에서 최적 선택 중...")
        
        # 소개팅/데이트 특화 우선순위
        if any(keyword in ['소개팅', '데이트'] for keyword in user_keywords):
            # 1순위: 소개팅 전용 조합 (스트라이프 셔츠 제외)
            for c in actual_combos:
                items = c['items'] if isinstance(c['items'], list) else [str(c['items'])]
                # 스트라이프 셔츠가 포함되지 않은 소개팅 조합 우선 선택
                if (c.get('occasion') and '소개팅' in c['occasion'].lower() and 
                    not any('스트라이프' in item for item in items)):
                    combo = c
                    print(f"✅ 소개팅 전용 조합 선택: '{c['combination']}' (스트라이프 셔츠 제외)")
                    break
            
            # 2순위: 일반적인 소개팅 조합
            if combo == actual_combos[0]:  # 아직 첫 번째 것 그대로라면
                for c in actual_combos:
                    if c.get('occasion') and '소개팅' in c['occasion'].lower():
                        combo = c
                        print(f"✅ 소개팅 조합 선택: '{c['combination']}'")
                        break
            
            # 3순위: 데이트 조합 (스트라이프 셔츠 제외)
            if combo == actual_combos[0]:  # 아직 첫 번째 것 그대로라면
                for c in actual_combos:
                    items = c['items'] if isinstance(c['items'], list) else [str(c['items'])]
                    if (c.get('occasion') and '데이트' in c['occasion'].lower() and 
                        not any('스트라이프' in item for item in items)):
                        combo = c
                        print(f"✅ 데이트 조합 선택: '{c['combination']}' (스트라이프 셔츠 제외)")
                        break
    
    # 선택된 조합 출력
    items_str = ', '.join(combo['items']) if isinstance(combo['items'], list) else str(combo['items'])
    print(f"\n🎯 최종 선택된 조합:")
    print(f"   조합명: {combo['combination']}")
    print(f"   아이템: {items_str}")
    print(f"   상황: {combo.get('occasion', 'N/A')}")
    
    # 스트라이프 셔츠 포함 여부 확인
    items = combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]
    has_stripe = any('스트라이프' in item for item in items)
    print(f"   스트라이프 셔츠 포함: {'❌' if not has_stripe else '⚠️'}")
    
else:
    print("매칭된 조합이 없습니다.") 