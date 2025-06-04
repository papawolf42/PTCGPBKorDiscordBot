"""
프로젝트 경로 관리 모듈

프로젝트 루트를 자동으로 찾고, 데이터 디렉토리 경로를 중앙에서 관리합니다.
"""
import os


def find_project_root():
    """
    프로젝트 루트를 찾는 함수
    
    CLAUDE.md와 requirements.txt 파일이 있는 디렉토리를 프로젝트 루트로 인식합니다.
    
    Returns:
        str: 프로젝트 루트 디렉토리 절대 경로
        
    Raises:
        RuntimeError: 프로젝트 루트를 찾을 수 없을 때
    """
    current = os.path.dirname(os.path.abspath(__file__))
    
    # 최상위 디렉토리까지 탐색
    while current != os.path.dirname(current):
        # CLAUDE.md와 requirements.txt가 모두 있는 디렉토리가 프로젝트 루트
        if (os.path.exists(os.path.join(current, 'CLAUDE.md')) and 
            os.path.exists(os.path.join(current, 'requirements.txt'))):
            return current
        current = os.path.dirname(current)
    
    raise RuntimeError(
        "프로젝트 루트를 찾을 수 없습니다! "
        "CLAUDE.md와 requirements.txt 파일이 있는지 확인하세요."
    )


# 프로젝트 루트 디렉토리
PROJECT_ROOT = find_project_root()

# 주요 디렉토리만 정의
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
TEST_DATA_DIR = os.path.join(PROJECT_ROOT, "data_test")


def ensure_directories(*subdirs):
    """
    필요한 디렉토리를 생성합니다.
    
    Args:
        *subdirs: DATA_DIR 하위에 생성할 디렉토리 이름들
                 비어있으면 기본 디렉토리들만 생성
    
    Example:
        ensure_directories()  # 기본 디렉토리만
        ensure_directories("heartbeat_data", "user_data", "raw")  # 특정 하위 디렉토리
    """
    # 기본 디렉토리는 항상 생성
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # 요청된 하위 디렉토리 생성
    for subdir in subdirs:
        dir_path = os.path.join(DATA_DIR, subdir)
        os.makedirs(dir_path, exist_ok=True)


def get_data_path(*paths):
    """
    데이터 디렉토리 기준 상대 경로를 절대 경로로 변환합니다.
    
    Args:
        *paths: 경로 구성 요소들
        
    Returns:
        str: 절대 경로
        
    Example:
        >>> get_data_path('heartbeat_data', 'user123.json')
        '/Users/papawolf/Dev/PTCGPBKorNew/data/heartbeat_data/user123.json'
    """
    return os.path.join(DATA_DIR, *paths)


def get_project_path(*paths):
    """
    프로젝트 루트 기준 상대 경로를 절대 경로로 변환합니다.
    
    Args:
        *paths: 경로 구성 요소들
        
    Returns:
        str: 절대 경로
    """
    return os.path.join(PROJECT_ROOT, *paths)


# 디버깅용: 모듈 import 시 경로 출력
if __name__ == "__main__":
    print(f"프로젝트 루트: {PROJECT_ROOT}")
    print(f"데이터 디렉토리: {DATA_DIR}")
    print(f"로그 디렉토리: {LOGS_DIR}")
    print(f"테스트 데이터: {TEST_DATA_DIR}")
    print("\n사용 예시:")
    print(f"  Heartbeat: os.path.join(DATA_DIR, 'heartbeat_data')")
    print(f"  사용자 데이터: os.path.join(DATA_DIR, 'user_data')")
    print(f"  Raw 데이터: os.path.join(DATA_DIR, 'raw')")