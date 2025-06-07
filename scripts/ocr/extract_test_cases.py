#!/usr/bin/env python3
"""
media.txt와 media2.txt 파일에서 FRIENDCODE 이미지와 관련 정보를 추출하여
테스트 케이스를 생성하는 스크립트
"""

import re
import json
from pathlib import Path

def parse_user_info(text):
    """사용자명과 친구코드를 한번에 추출"""
    # 패턴: username숫자 (16자리숫자) 형식
    # 예: laff155 (6855906683167259)
    # 예: yunpac426 (9053874066196496)
    pattern = r'(\w+)\s*\((\d{16})\)'
    match = re.search(pattern, text)
    
    if match:
        username_with_num = match.group(1)
        friend_code_raw = match.group(2)
        
        # 사용자명에서 숫자 제거 (끝의 숫자만)
        username = re.sub(r'\d+$', '', username_with_num)
        if not username:  # 전부 숫자인 경우
            username = username_with_num
        
        # 16자리 숫자를 4-4-4-4 형식으로 변환
        if len(friend_code_raw) == 16:
            friend_code = f"{friend_code_raw[0:4]}-{friend_code_raw[4:8]}-{friend_code_raw[8:12]}-{friend_code_raw[12:16]}"
        else:
            friend_code = friend_code_raw
            
        return username, friend_code
    
    return None, None

def extract_friend_code(text):
    """텍스트에서 친구코드 패턴을 추출 (백업용)"""
    # 친구코드 패턴: 4자리-4자리-4자리-4자리
    pattern = r'\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}'
    match = re.search(pattern, text)
    if match:
        # 하이픈으로 정규화
        return re.sub(r'[-\s]+', '-', match.group())
    
    # 16자리 연속 숫자 패턴
    pattern2 = r'\b\d{16}\b'
    match2 = re.search(pattern2, text)
    if match2:
        raw = match2.group()
        return f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
    
    return None

def extract_username(text):
    """텍스트에서 사용자명 추출 (백업용)"""
    # @mention 패턴 우선
    mention_match = re.search(r'@(\w+)', text)
    if mention_match:
        return mention_match.group(1)
    
    # 사용자명 (숫자) 패턴
    user_match = re.search(r'(\w+)\s*\(\d+\)', text)
    if user_match:
        username = user_match.group(1)
        # 끝의 숫자 제거
        return re.sub(r'\d+$', '', username) or username
    
    return None

def parse_media_file(filepath):
    """media.txt 파일을 파싱하여 테스트 케이스 추출"""
    test_cases = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 메시지 블록으로 분리 (날짜 패턴으로 분리)
    message_blocks = re.split(r'\n\[20\d{2}\.\s*\d{1,2}\.\s*\d{1,2}\.\s*[^\]]+\]', content)
    
    for i, block in enumerate(message_blocks):
        if '{Attachments}' in block and 'FRIENDCODE' in block:
            # 현재 블록과 이전 블록을 합쳐서 검색
            combined_text = block
            if i > 0:
                combined_text = message_blocks[i-1] + '\n' + block
            
            # 사용자명과 친구코드를 한번에 추출
            username, friend_code = parse_user_info(combined_text)
            
            # 백업 방법으로 다시 시도
            if not username:
                username = extract_username(combined_text)
            if not friend_code:
                friend_code = extract_friend_code(combined_text)
            
            # FRIENDCODE 이미지 파일명 추출
            friendcode_pattern = r'(media\d?/)?(\d+_\d+_FRIENDCODE_\d+_packs-\w+\.png)'
            matches = re.findall(friendcode_pattern, block)
            
            for match in matches:
                filename = match[1]
                if username and friend_code:
                    # 한글 사용자명은 UNKNOWN으로 처리
                    if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in username):
                        username = 'UNKNOWN'
                    test_cases.append({
                        'filename': filename,
                        'username': username,
                        'friend_code': friend_code
                    })
                elif username or friend_code:
                    # 부분적으로라도 정보가 있으면 저장
                    test_cases.append({
                        'filename': filename,
                        'username': username or 'UNKNOWN',
                        'friend_code': friend_code or 'UNKNOWN'
                    })
    
    return test_cases

def main():
    """메인 실행 함수"""
    project_root = Path(__file__).parent.parent.parent
    media_files = [
        project_root / "DATA_DETECT" / "media.txt",
        project_root / "DATA_DETECT" / "media2.txt"
    ]
    
    all_test_cases = []
    
    for media_file in media_files:
        if media_file.exists():
            print(f"파싱 중: {media_file}")
            test_cases = parse_media_file(media_file)
            all_test_cases.extend(test_cases)
            print(f"  - {len(test_cases)}개 테스트 케이스 추출")
    
    # 중복 제거
    unique_cases = {}
    for case in all_test_cases:
        filename = case['filename']
        if filename not in unique_cases:
            unique_cases[filename] = case
    
    # 결과 저장
    output_file = Path(__file__).parent / "test_cases.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(list(unique_cases.values()), f, ensure_ascii=False, indent=2)
    
    print(f"\n총 {len(unique_cases)}개의 유니크한 테스트 케이스 저장됨: {output_file}")
    
    # Python 코드 형식으로도 출력
    print("\n테스트 케이스 (Python 코드):")
    print("test_cases = [")
    for case in list(unique_cases.values())[:10]:  # 처음 10개만 출력
        print(f'    ("{case["filename"]}", "{case["username"]}", "{case["friend_code"]}"),')
    print("    # ... 더 많은 케이스들")
    print("]")

if __name__ == "__main__":
    main()