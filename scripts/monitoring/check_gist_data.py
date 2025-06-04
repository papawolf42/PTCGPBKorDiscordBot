#!/usr/bin/env python3
"""
check_gist_data.py - Gist에 저장된 데이터 확인
"""

import os
from dotenv import load_dotenv
import GIST

# .env 파일 로드
load_dotenv()

# 환경변수 로드
GITHUB_TOKEN = os.getenv("GITHUB_GIST_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER_ID")
GIST_ID_1 = os.getenv("GIST_ID_1")
GIST_ID_2 = os.getenv("GIST_ID_2")
GIST_ID_3 = os.getenv("GIST_ID_3")

def check_gist_files():
    """Gist에 있는 파일들 확인"""
    
    print("=== Gist 파일 확인 ===")
    
    # Gist ID별로 확인
    gist_ids = {
        "GIST_ID_1": GIST_ID_1,
        "GIST_ID_2": GIST_ID_2,
        "GIST_ID_3": GIST_ID_3
    }
    
    for name, gist_id in gist_ids.items():
        print(f"\n{name}: {gist_id}")
        
        try:
            # GIST API를 통해 파일 목록 가져오기
            import requests
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            response = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers)
            
            if response.status_code == 200:
                gist_data = response.json()
                files = gist_data.get('files', {})
                
                print(f"  파일 수: {len(files)}")
                for filename in files:
                    file_info = files[filename]
                    size = file_info.get('size', 0)
                    print(f"  - {filename} ({size} bytes)")
                    
                    # 파일 내용 미리보기 (처음 100자)
                    if size > 0:
                        content = file_info.get('content', '')
                        preview = content[:100] + '...' if len(content) > 100 else content
                        # 줄바꿈 제거
                        preview = preview.replace('\n', ' ')
                        print(f"    내용: {preview}")
            else:
                print(f"  ❌ 접근 실패: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 에러: {e}")

def test_gist_access():
    """GIST 모듈로 직접 접근 테스트"""
    print("\n\n=== GIST 모듈 접근 테스트 ===")
    
    # Group7과 Group8 파일들 테스트
    test_files = [
        ("Group7_Admin", "TEXT"),
        ("Group7_member", "JSON"),
        ("Group8_Admin", "TEXT"),
        ("Group8_member", "JSON")
    ]
    
    for filename, format_type in test_files:
        print(f"\n{filename} ({format_type}):")
        try:
            if format_type == "TEXT":
                obj = GIST.TEXT(GIST_ID_1, filename, INITIAL=True)
                if obj.DATA:
                    print(f"  데이터 수: {len(obj.DATA)} 줄")
                    # 처음 3개만 출력
                    for i, item in enumerate(list(obj.DATA)[:3]):
                        print(f"    {i+1}. {item}")
                else:
                    print("  데이터 없음")
            else:
                obj = GIST.JSON(GIST_ID_1, filename, INITIAL=True)
                if obj.DATA:
                    print(f"  데이터 수: {len(obj.DATA)} 항목")
                    # 처음 3개 키만 출력
                    for i, key in enumerate(list(obj.DATA.keys())[:3]):
                        print(f"    {i+1}. {key}")
                else:
                    print("  데이터 없음")
        except Exception as e:
            print(f"  ❌ 에러: {e}")

if __name__ == "__main__":
    # 환경변수 확인
    print("환경변수 확인:")
    print(f"GITHUB_USER_ID: {GITHUB_USER}")
    print(f"GIST_ID_1: {GIST_ID_1}")
    print(f"GIST_ID_2: {GIST_ID_2}")
    print(f"GIST_ID_3: {GIST_ID_3}")
    print(f"Token 설정: {'Yes' if GITHUB_TOKEN else 'No'}")
    
    check_gist_files()
    test_gist_access()