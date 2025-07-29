import json
import os

def test_json_loading_direct():
    """서비스와 동일한 방식으로 JSON 로딩 테스트"""
    print("Testing JSON loading like the service does")
    
    # 서비스와 동일한 초기화
    reference_data = {
        "fashion_items": [],
        "outfit_combinations": [],
        "styling_tips": [],
        "color_recommendations": [],
        "seasonal_advice": []
    }
    
    pipeline_dir = r"C:\fashion_summary"
    
    print(f"Searching JSON files in: {pipeline_dir}")
    print(f"Directory exists: {os.path.exists(pipeline_dir)}")
    
    try:
        json_files_found = 0
        successful_loads = 0
        
        for filename in os.listdir(pipeline_dir):
            if filename.endswith('.json') and filename.startswith('fashion_extract_'):
                json_files_found += 1
                file_path = os.path.join(pipeline_dir, filename)
                print(f"Processing: {filename}")
                
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
                
                if not data:
                    print(f"  Failed to read: {filename}")
                    continue
                
                if 'fashion_data' in data:
                    successful_loads += 1
                    fashion_data = data['fashion_data']
                    
                    # 데이터 수집
                    if 'fashion_items' in fashion_data:
                        reference_data['fashion_items'].extend(fashion_data['fashion_items'])
                        print(f"  Added {len(fashion_data['fashion_items'])} fashion items")
                    
                    if 'outfit_combinations' in fashion_data:
                        reference_data['outfit_combinations'].extend(fashion_data['outfit_combinations'])
                        print(f"  Added {len(fashion_data['outfit_combinations'])} outfit combinations")
                    
                    if 'color_recommendations' in fashion_data:
                        reference_data['color_recommendations'].extend(fashion_data['color_recommendations'])
                        print(f"  Added {len(fashion_data['color_recommendations'])} color recommendations")
                    
                    if 'styling_tips' in fashion_data:
                        reference_data['styling_tips'].extend(fashion_data['styling_tips'])
                        print(f"  Added {len(fashion_data['styling_tips'])} styling tips")
                else:
                    print(f"  No fashion_data key in: {filename}")
        
        print(f"\nFinal results:")
        print(f"  JSON files found: {json_files_found}")
        print(f"  Successfully loaded: {successful_loads}")
        print(f"  Total fashion items: {len(reference_data['fashion_items'])}")
        print(f"  Total outfit combinations: {len(reference_data['outfit_combinations'])}")
        print(f"  Total color recommendations: {len(reference_data['color_recommendations'])}")
        print(f"  Total styling tips: {len(reference_data['styling_tips'])}")
        
        # 샘플 데이터 확인
        if reference_data['outfit_combinations']:
            print(f"\nSample outfit combination:")
            print(f"  {reference_data['outfit_combinations'][0]}")
        
        if reference_data['fashion_items']:
            print(f"\nSample fashion item:")
            print(f"  {reference_data['fashion_items'][0]}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_loading_direct() 