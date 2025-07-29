import json
import os

def debug_json_loading():
    """JSON 데이터 로딩만 디버깅"""
    print("🔍 JSON 데이터 로딩 디버깅")
    
    pipeline_dir = r"C:\fashion_summary"
    
    if not os.path.exists(pipeline_dir):
        print(f"❌ 디렉토리가 존재하지 않음: {pipeline_dir}")
        return
    
    # JSON 데이터 수집
    all_fashion_items = []
    all_outfit_combinations = []
    all_color_recommendations = []
    all_styling_tips = []
    
    json_files_found = 0
    successful_loads = 0
    
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            json_files_found += 1
            file_path = os.path.join(pipeline_dir, filename)
            print(f"\n📄 처리 중: {filename}")
            
            try:
                # 여러 인코딩으로 시도
                encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
                data = None
                used_encoding = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            data = json.load(f)
                            used_encoding = encoding
                            break
                    except:
                        continue
                
                if data and 'fashion_data' in data:
                    successful_loads += 1
                    fashion_data = data['fashion_data']
                    
                    # 데이터 수집
                    if 'fashion_items' in fashion_data:
                        all_fashion_items.extend(fashion_data['fashion_items'])
                        print(f"   ✅ 패션 아이템 {len(fashion_data['fashion_items'])}개 추가")
                    
                    if 'outfit_combinations' in fashion_data:
                        all_outfit_combinations.extend(fashion_data['outfit_combinations'])
                        print(f"   ✅ 아웃핏 조합 {len(fashion_data['outfit_combinations'])}개 추가")
                    
                    if 'color_recommendations' in fashion_data:
                        all_color_recommendations.extend(fashion_data['color_recommendations'])
                        print(f"   ✅ 컬러 추천 {len(fashion_data['color_recommendations'])}개 추가")
                    
                    if 'styling_tips' in fashion_data:
                        all_styling_tips.extend(fashion_data['styling_tips'])
                        print(f"   ✅ 스타일링 팁 {len(fashion_data['styling_tips'])}개 추가")
                    
                    print(f"   📝 인코딩: {used_encoding}")
                else:
                    print(f"   ❌ fashion_data 키가 없음")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
    
    print(f"\n📊 최종 결과:")
    print(f"   - JSON 파일 수: {json_files_found}개")
    print(f"   - 성공적으로 로드된 파일: {successful_loads}개")
    print(f"   - 총 패션 아이템: {len(all_fashion_items)}개")
    print(f"   - 총 아웃핏 조합: {len(all_outfit_combinations)}개")
    print(f"   - 총 컬러 추천: {len(all_color_recommendations)}개")
    print(f"   - 총 스타일링 팁: {len(all_styling_tips)}개")
    
    # 샘플 데이터 출력
    if all_outfit_combinations:
        print(f"\n🎯 샘플 아웃핏 조합:")
        for i, combo in enumerate(all_outfit_combinations[:3]):
            print(f"   {i+1}. {combo}")
    
    if all_fashion_items:
        print(f"\n👕 샘플 패션 아이템:")
        for i, item in enumerate(all_fashion_items[:3]):
            print(f"   {i+1}. {item}")
    
    if all_color_recommendations:
        print(f"\n🎨 샘플 컬러 추천:")
        for i, color in enumerate(all_color_recommendations[:3]):
            print(f"   {i+1}. {color}")

if __name__ == "__main__":
    debug_json_loading() 