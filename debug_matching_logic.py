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
                if 'fashion_data' in json_data:
                    if 'outfit_combinations' in json_data['fashion_data']:
                        data['outfit_combinations'].extend(json_data['fashion_data']['outfit_combinations'])
        except:
            continue

# 실제 사용자 입력으로 테스트
test_input = "내일 소개팅 가는데 옷 추천해줘"
user_keywords = test_input.lower().split()

# 키워드 확장
expanded_keywords = user_keywords.copy()
for keyword in user_keywords:
    if keyword == '소개팅':
        expanded_keywords.extend(['소개팅', '데이트', '미팅'])

print(f"원본 키워드: {user_keywords}")
print(f"확장된 키워드: {expanded_keywords}")

# 매칭 과정 상세 분석
print("\n" + "="*60)
print("매칭 과정 상세 분석:")
print("="*60)

actual_combos = []

for combo in data['outfit_combinations']:
    items_list = combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]
    occasion_str = ""
    if combo['occasion'] is not None:
        if isinstance(combo['occasion'], str):
            occasion_str = combo['occasion'].lower()
        else:
            occasion_str = str(combo['occasion']).lower()
    
    # 각 조건을 개별적으로 확인
    items_match = any(any(keyword in item.lower() for keyword in expanded_keywords) for item in items_list)
    occasion_match = any(keyword in occasion_str for keyword in expanded_keywords) if occasion_str else False
    
    # 소개팅 관련 조합들만 상세 분석
    if '소개팅' in occasion_str or '데이트' in occasion_str:
        print(f"\n🔍 조합: {combo['combination']}")
        print(f"   아이템: {items_list}")
        print(f"   상황: {combo.get('occasion', 'N/A')}")
        print(f"   items_match: {items_match}")
        print(f"   occasion_match: {occasion_match}")
        
        if items_match or occasion_match:
            actual_combos.append(combo)
            print(f"   ✅ 매칭됨!")
        else:
            print(f"   ❌ 매칭 안됨")
    
    # 다른 조합들도 확인
    elif items_match or occasion_match:
        actual_combos.append(combo)

print(f"\n🎯 최종 매칭된 조합: {len(actual_combos)}개")
for i, combo in enumerate(actual_combos, 1):
    items_str = ', '.join(combo['items']) if isinstance(combo['items'], list) else str(combo['items'])
    has_stripe = any('스트라이프' in item for item in (combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]))
    print(f"{i}. {combo['combination']} (스트라이프: {'예' if has_stripe else '아니오'})")
    print(f"   아이템: {items_str}")
    print(f"   상황: {combo.get('occasion', 'N/A')}")
    print()

# 소개팅 관련 모든 조합 확인
print("="*60)
print("소개팅 관련 모든 조합 (매칭 여부와 관계없이):")
print("="*60)

sogeting_all = []
for combo in data['outfit_combinations']:
    occasion = str(combo.get('occasion', '')).lower()
    if '소개팅' in occasion or '데이트' in occasion:
        sogeting_all.append(combo)

for i, combo in enumerate(sogeting_all, 1):
    items_str = ', '.join(combo['items']) if isinstance(combo['items'], list) else str(combo['items'])
    has_stripe = any('스트라이프' in item for item in (combo['items'] if isinstance(combo['items'], list) else [str(combo['items'])]))
    is_matched = combo in actual_combos
    print(f"{i}. {combo['combination']} (매칭: {'✅' if is_matched else '❌'}, 스트라이프: {'예' if has_stripe else '아니오'})")
    print(f"   아이템: {items_str}")
    print(f"   상황: {combo.get('occasion', 'N/A')}")
    print() 