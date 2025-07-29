import json
import os

def check_sogeting_data():
    """소개팅 관련 데이터 확인"""
    print("소개팅 관련 데이터 확인")
    
    pipeline_dir = r"C:\fashion_summary"
    sogeting_combos = []
    
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            file_path = os.path.join(pipeline_dir, filename)
            
            try:
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
                    fashion_data = data['fashion_data']
                    
                    if 'outfit_combinations' in fashion_data:
                        for combo in fashion_data['outfit_combinations']:
                            occasion = combo.get('occasion', '')
                            if isinstance(occasion, str) and '소개팅' in occasion.lower():
                                sogeting_combos.append({
                                    'file': filename,
                                    'combination': combo['combination'],
                                    'items': combo['items'],
                                    'occasion': combo['occasion']
                                })
                        
            except Exception as e:
                print(f"Error with {filename}: {e}")
    
    print(f"\n소개팅 관련 조합 {len(sogeting_combos)}개 발견:")
    for i, combo in enumerate(sogeting_combos):
        print(f"\n{i+1}. 파일: {combo['file']}")
        print(f"   조합: {combo['combination']}")
        print(f"   아이템: {combo['items']}")
        print(f"   상황: {combo['occasion']}")
    
    # 전체 조합도 확인
    print(f"\n전체 조합 확인:")
    all_combos = []
    
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            file_path = os.path.join(pipeline_dir, filename)
            
            try:
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
                    fashion_data = data['fashion_data']
                    
                    if 'outfit_combinations' in fashion_data:
                        for combo in fashion_data['outfit_combinations']:
                            all_combos.append({
                                'combination': combo['combination'],
                                'occasion': combo.get('occasion', '')
                            })
                        
            except Exception as e:
                continue
    
    print(f"전체 조합 {len(all_combos)}개:")
    for i, combo in enumerate(all_combos[:10]):  # 처음 10개만
        print(f"  {i+1}. {combo['combination']} - {combo['occasion']}")

if __name__ == "__main__":
    check_sogeting_data() 