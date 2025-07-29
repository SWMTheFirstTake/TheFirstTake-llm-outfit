import json
import os
import codecs

def fix_json_encoding():
    """JSON 파일들의 인코딩 문제를 해결"""
    pipeline_dir = r"C:\fashion_summary"
    
    print("🔧 JSON 파일 인코딩 수정 시작")
    
    fixed_count = 0
    for filename in os.listdir(pipeline_dir):
        if filename.endswith('.json') and filename.startswith('fashion_extract_'):
            file_path = os.path.join(pipeline_dir, filename)
            print(f"📄 처리 중: {filename}")
            
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
                
                if data and used_encoding != 'utf-8':
                    # UTF-8로 다시 저장
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"   ✅ 인코딩 수정 완료: {used_encoding} → utf-8")
                    fixed_count += 1
                elif data:
                    print(f"   ✅ 이미 UTF-8 인코딩")
                else:
                    print(f"   ❌ 읽기 실패")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
    
    print(f"\n🎉 완료: {fixed_count}개 파일 인코딩 수정됨")

if __name__ == "__main__":
    fix_json_encoding() 