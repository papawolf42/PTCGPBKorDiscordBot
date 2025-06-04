#!/usr/bin/env python3
"""
copy_to_test.py - 실제 데이터를 테스트 환경으로 복사하는 스크립트
"""

import os
import shutil
import json
from pathlib import Path

def copy_to_test():
    """실제 데이터를 테스트 환경으로 복사"""
    
    # 경로 설정
    source_dir = Path("/Users/papawolf/Dev/PTCGPBKor/data/poke_data")
    target_dir = Path("/Users/papawolf/Dev/PTCGPBKor/data_test/poke_data")
    
    print("=== 실제 데이터 → 테스트 환경 복사 시작 ===")
    
    # 테스트 디렉토리 생성
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 복사할 디렉토리 목록
    dirs_to_copy = ["common", "group7", "group8"]
    
    for dir_name in dirs_to_copy:
        source_path = source_dir / dir_name
        target_path = target_dir / dir_name
        
        if source_path.exists():
            # 기존 테스트 데이터 삭제
            if target_path.exists():
                shutil.rmtree(target_path)
            
            # 디렉토리 복사
            shutil.copytree(source_path, target_path)
            print(f"✅ {dir_name} 복사 완료")
            
            # 파일 목록 출력
            for file in target_path.iterdir():
                if file.is_file():
                    print(f"   - {file.name}")
        else:
            print(f"⚠️  {dir_name} 소스 디렉토리 없음")
    
    # admin.txt 수정 (테스트용 ID로 변경)
    admin_path = target_dir / "common" / "admin.txt"
    if admin_path.exists():
        with open(admin_path, 'w') as f:
            f.write("396176142333378562")  # papawolf의 Discord ID
        print("\n✅ admin.txt를 테스트용 ID로 수정")
    
    print(f"\n데이터 복사 완료: {target_dir}")

if __name__ == "__main__":
    copy_to_test()