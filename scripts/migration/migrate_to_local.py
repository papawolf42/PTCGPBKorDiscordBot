#!/usr/bin/env python3
"""
migrate_to_local.py - GitHub Gist 데이터를 로컬 파일로 마이그레이션하는 스크립트
"""

import os
import json
import datetime
from dotenv import load_dotenv
import GIST
from LocalFile import LocalFile

# .env 파일 로드
load_dotenv()

# 환경변수 로드
GITHUB_TOKEN = os.getenv("GITHUB_GIST_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER_ID")
GIST_ID_1 = os.getenv("GIST_ID_1")
GIST_ID_2 = os.getenv("GIST_ID_2")
GIST_ID_3 = os.getenv("GIST_ID_3")

def migrate_data():
    """Gist 데이터를 로컬 파일로 마이그레이션"""
    
    print("=== GitHub Gist → 로컬 파일 마이그레이션 시작 ===")
    print(f"시작 시간: {datetime.datetime.now()}")
    
    # LocalFile 인스턴스 생성
    local_storage = LocalFile(test_mode=False)  # 실제 데이터 경로 사용
    
    # 마이그레이션할 데이터 목록 (Poke.py의 실제 사용 패턴에 맞춤)
    migration_list = [
        # 공통 데이터 (GIST_ID_1)
        {
            'gist_id': GIST_ID_1,
            'group': 'Common',
            'files': [
                ('Admin', 'TEXT', 'admin'),           # Admin -> admin.txt
                ('Alliance', 'JSON', 'member')        # Alliance -> member.json
            ]
        },
        # Group7 데이터
        {
            'gist_id': GIST_ID_2,
            'group': 'Group7',
            'files': [
                ('Group7', 'TEXT', 'online')          # Group7 -> online.txt
            ]
        },
        {
            'gist_id': GIST_ID_3,
            'group': 'Group7',
            'files': [
                ('GodPack7', 'JSON', 'godpack'),      # GodPack7 -> godpack.json
                ('Code7', 'JSON', 'godpackCode')      # Code7 -> godpackCode.json
            ]
        },
        # Group8 데이터
        {
            'gist_id': GIST_ID_2,
            'group': 'Group8',
            'files': [
                ('Group8', 'TEXT', 'online')          # Group8 -> online.txt
            ]
        },
        {
            'gist_id': GIST_ID_3,
            'group': 'Group8',
            'files': [
                ('GodPack8', 'JSON', 'godpack'),      # GodPack8 -> godpack.json
                ('Code8', 'JSON', 'godpackCode')      # Code8 -> godpackCode.json
            ]
        }
    ]
    
    success_count = 0
    fail_count = 0
    
    for migration in migration_list:
        print(f"\n--- {migration['group']} 마이그레이션 시작 ---")
        
        for file_info in migration['files']:
            if len(file_info) == 3:
                filename, format_type, save_as = file_info
            else:
                filename, format_type = file_info
                save_as = filename
            try:
                # Gist에서 데이터 읽기
                if format_type == 'TEXT':
                    gist_obj = GIST.TEXT(migration['gist_id'], filename, INITIAL=True)
                    data = list(gist_obj.DATA) if gist_obj.DATA else []
                else:
                    gist_obj = GIST.JSON(migration['gist_id'], filename, INITIAL=True)
                    data = gist_obj.DATA if gist_obj.DATA else {}
                
                # 데이터가 없으면 스킵
                if not data:
                    print(f"  ⚠️  {filename}: 데이터 없음 (스킵)")
                    continue
                
                # 로컬 파일로 저장 (save_as 이름 사용)
                save_filename = f"{migration['group']}_{save_as}"
                success = local_storage.uploadFile(migration['group'], save_filename, data, format_type)
                
                if success:
                    print(f"  ✅ {filename} → {save_filename}: 마이그레이션 성공")
                    success_count += 1
                    
                    # 검증: 저장된 데이터 다시 읽어서 비교
                    saved_data = local_storage.openFile(migration['group'], save_filename, format_type)
                    if format_type == 'JSON':
                        if saved_data == data:
                            print(f"     ✓ 데이터 검증 성공")
                        else:
                            print(f"     ✗ 데이터 검증 실패!")
                    else:
                        # TEXT 형식은 리스트로 변환되므로 다시 문자열로 변환해서 비교
                        if isinstance(saved_data, list):
                            saved_str = '\n'.join(saved_data)
                            original_str = '\n'.join(data) if isinstance(data, list) else data
                            if saved_str == original_str or saved_data == data:
                                print(f"     ✓ 데이터 검증 성공")
                            else:
                                print(f"     ✗ 데이터 검증 실패!")
                else:
                    print(f"  ❌ {filename}: 마이그레이션 실패")
                    fail_count += 1
                    
            except Exception as e:
                print(f"  ❌ {filename}: 에러 발생 - {str(e)}")
                fail_count += 1
    
    # 백업 생성
    print("\n--- 백업 생성 중 ---")
    backup_success = local_storage.backup()
    if backup_success:
        print("✅ 백업 생성 완료")
    else:
        print("❌ 백업 생성 실패")
    
    # 마이그레이션 결과 출력
    print("\n=== 마이그레이션 완료 ===")
    print(f"종료 시간: {datetime.datetime.now()}")
    print(f"성공: {success_count}개 파일")
    print(f"실패: {fail_count}개 파일")
    print(f"\n데이터 저장 위치: {local_storage.base_path}")
    
    # 마이그레이션 로그 저장
    log_data = {
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'success_count': success_count,
        'fail_count': fail_count,
        'data_path': local_storage.base_path
    }
    
    log_path = os.path.join(local_storage.base_path, 'migration_log.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"마이그레이션 로그 저장: {log_path}")
    
    return success_count, fail_count

def verify_migration():
    """마이그레이션된 데이터 검증"""
    print("\n=== 마이그레이션 데이터 검증 ===")
    
    local_storage = LocalFile(test_mode=False)
    
    # 검증할 파일 목록
    files_to_check = [
        ('Group7', 'Group7_Admin', 'TEXT'),
        ('Group7', 'Group7_online', 'TEXT'),
        ('Group7', 'Group7_member', 'JSON'),
        ('Group7', 'Group7_godpack', 'JSON'),
        ('Group7', 'Group7_godpackCode', 'JSON'),
        ('Group8', 'Group8_Admin', 'TEXT'),
        ('Group8', 'Group8_online', 'TEXT'),
        ('Group8', 'Group8_member', 'JSON'),
        ('Group8', 'Group8_godpack', 'JSON'),
        ('Group8', 'Group8_godpackCode', 'JSON')
    ]
    
    for group, filename, format_type in files_to_check:
        if local_storage.exists(group, filename):
            data = local_storage.openFile(group, filename, format_type)
            if data is not None:
                if format_type == 'JSON':
                    if isinstance(data, dict):
                        print(f"✅ {filename}: {len(data)} 항목")
                    elif isinstance(data, list):
                        print(f"✅ {filename}: {len(data)} 항목")
                else:
                    if isinstance(data, list):
                        print(f"✅ {filename}: {len(data)} 줄")
                    else:
                        print(f"✅ {filename}: 빈 파일")
            else:
                print(f"❌ {filename}: 읽기 실패")
        else:
            print(f"⚠️  {filename}: 파일 없음")

if __name__ == "__main__":
    # 마이그레이션 실행
    success, fail = migrate_data()
    
    # 데이터 검증
    if success > 0:
        verify_migration()
    
    print("\n마이그레이션 스크립트 종료")