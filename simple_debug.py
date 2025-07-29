import json
import os

def simple_debug():
    print("JSON 데이터 로딩 확인")
    
    pipeline_dir = r"C:\fashion_summary"
    
    if not os.path.exists(pipeline_dir):
        print(f"Directory not found: {pipeline_dir}")
        return
    
    all_fashion_items = []
    all_outfit_combinations = []
    all_color_recommendations = []
    
    json_files_found = 0
    successful_loads = 0
    
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            json_files_found += 1
            file_path = os.path.join(pipeline_dir, filename)
            
            try:
                # 여러 인코딩으로 시도
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
                    successful_loads += 1
                    fashion_data = data['fashion_data']
                    
                    if 'fashion_items' in fashion_data:
                        all_fashion_items.extend(fashion_data['fashion_items'])
                    
                    if 'outfit_combinations' in fashion_data:
                        all_outfit_combinations.extend(fashion_data['outfit_combinations'])
                    
                    if 'color_recommendations' in fashion_data:
                        all_color_recommendations.extend(fashion_data['color_recommendations'])
                        
            except Exception as e:
                print(f"Error with {filename}: {e}")
    
    print(f"JSON files found: {json_files_found}")
    print(f"Successfully loaded: {successful_loads}")
    print(f"Total fashion items: {len(all_fashion_items)}")
    print(f"Total outfit combinations: {len(all_outfit_combinations)}")
    print(f"Total color recommendations: {len(all_color_recommendations)}")
    
    # 샘플 데이터 출력
    if all_outfit_combinations:
        print(f"\nSample outfit combinations:")
        for i, combo in enumerate(all_outfit_combinations[:3]):
            print(f"  {i+1}. {combo}")
    
    if all_fashion_items:
        print(f"\nSample fashion items:")
        for i, item in enumerate(all_fashion_items[:3]):
            print(f"  {i+1}. {item}")

if __name__ == "__main__":
    simple_debug() 