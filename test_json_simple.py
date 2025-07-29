import json
import os

def test_json_files():
    print("🔍 JSON 파일 테스트 시작")
    
    pipeline_dir = r"C:\fashion_summary"
    
    if not os.path.exists(pipeline_dir):
        print(f"❌ 디렉토리가 존재하지 않음: {pipeline_dir}")
        return
    
    json_files_found = 0
    total_fashion_items = 0
    total_outfit_combinations = 0
    total_color_recommendations = 0
    
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            json_files_found += 1
            file_path = os.path.join(pipeline_dir, filename)
            print(f"\n📄 JSON 파일 분석 중: {filename}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'fashion_data' in data:
                        fashion_data = data['fashion_data']
                        
                        # 패션 아이템들
                        if 'fashion_items' in fashion_data:
                            items_count = len(fashion_data['fashion_items'])
                            total_fashion_items += items_count
                            print(f"   ✅ 패션 아이템 {items_count}개")
                            if items_count > 0:
                                print(f"      첫 번째 아이템: {fashion_data['fashion_items'][0]}")
                        
                        # 아웃핏 조합들
                        if 'outfit_combinations' in fashion_data:
                            combos_count = len(fashion_data['outfit_combinations'])
                            total_outfit_combinations += combos_count
                            print(f"   ✅ 아웃핏 조합 {combos_count}개")
                            if combos_count > 0:
                                print(f"      첫 번째 조합: {fashion_data['outfit_combinations'][0]}")
                        
                        # 컬러 추천들
                        if 'color_recommendations' in fashion_data:
                            colors_count = len(fashion_data['color_recommendations'])
                            total_color_recommendations += colors_count
                            print(f"   ✅ 컬러 추천 {colors_count}개")
                            if colors_count > 0:
                                print(f"      첫 번째 컬러: {fashion_data['color_recommendations'][0]}")
                    else:
                        print(f"   ⚠️ fashion_data 키가 없음")
                        
            except Exception as e:
                print(f"   ❌ 파일 읽기 오류: {e}")
    
    print(f"\n📊 전체 통계:")
    print(f"   - JSON 파일 수: {json_files_found}개")
    print(f"   - 총 패션 아이템: {total_fashion_items}개")
    print(f"   - 총 아웃핏 조합: {total_outfit_combinations}개")
    print(f"   - 총 컬러 추천: {total_color_recommendations}개")

if __name__ == "__main__":
    test_json_files() 