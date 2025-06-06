# Poke.py 서버별 설정 파일
from datetime import timedelta

# 시간 상수 정의 (가독성을 위해)
MINUTES_3 = timedelta(minutes=3)
MINUTES_6 = timedelta(minutes=6) 
MINUTES_12 = timedelta(minutes=12)
HOURS_6 = timedelta(hours=6)
HOURS_12 = timedelta(hours=12)
HOURS_24 = timedelta(hours=24)
HOURS_36 = timedelta(hours=36)
DAYS_7 = timedelta(days=7)

# 갓팩 설정 (Group7용)
GODPACK_CONFIG = {
    # Yet → Bad 자동 변경 시간
    "time_threshold": {
        "1P": HOURS_24,
        "2P": HOURS_24,
        "3P": HOURS_24,
        "4P": HOURS_36,  # 사용하지 않지만 기본값
        "5P": HOURS_36,  # 사용하지 않지만 기본값
    },
    
    # 👎 반응 개수 임계값  
    "bad_threshold": {
        "2P": 5,
        "3P": 8,
        "4P": 11,  # 사용하지 않지만 기본값
        "5P": 14,  # 사용하지 않지만 기본값
    },
    
    # 특수 조건
    "no_reaction_time": HOURS_12,      # 반응 없을 때 Bad로 변경
    "only_question_time": HOURS_12,    # ❓만 있을 때 Bad로 변경
    "min_question_count": 3,            # ❓ 최소 개수
    
    # Bad 팩 삭제 시간
    "bad_delete_time": DAYS_7,
}

# 20% 팩 설정 (Group8용)
PACK20_CONFIG = {
    # Yet → Bad 자동 변경 시간
    "time_threshold": {
        "1P": HOURS_12,
        "2P": HOURS_12,
        "3P": HOURS_12,
        "4P": HOURS_12,  # 기본값
        "5P": HOURS_12,  # 기본값
    },
    
    # 👎 반응 개수 임계값
    "bad_threshold": {
        "2P": 3,
        "3P": 5,
        "4P": 7,   # 기본값
        "5P": 9,   # 기본값
    },
    
    # 특수 조건
    "no_reaction_time": HOURS_6,       # 반응 없을 때 Bad로 변경
    "only_question_time": HOURS_6,     # ❓만 있을 때 Bad로 변경
    "min_question_count": 2,            # ❓ 최소 개수
    
    # Bad 팩 삭제 시간
    "bad_delete_time": HOURS_24,
}

# 테스트 서버 설정
TEST_CONFIG = {
    # Yet → Bad 자동 변경 시간
    "time_threshold": {
        "1P": MINUTES_6,
        "2P": MINUTES_6,
        "3P": MINUTES_6,
        "4P": MINUTES_6,
        "5P": MINUTES_6,
    },
    
    # 👎 반응 개수 임계값
    "bad_threshold": {
        "2P": 2,
        "3P": 3,
        "4P": 4,
        "5P": 5,
    },
    
    # 특수 조건
    "no_reaction_time": MINUTES_3,     # 반응 없을 때 Bad로 변경
    "only_question_time": MINUTES_3,   # ❓만 있을 때 Bad로 변경
    "min_question_count": 1,            # ❓ 최소 개수
    
    # Bad 팩 삭제 시간
    "bad_delete_time": MINUTES_12,
}

# 설정 선택 함수
def get_config(server_name):
    """서버 이름에 따라 적절한 설정 반환"""
    configs = {
        "Group7": GODPACK_CONFIG,
        "Group8": PACK20_CONFIG,
        "GroupTest": TEST_CONFIG,
    }
    return configs.get(server_name, GODPACK_CONFIG)  # 기본값은 GODPACK

# 헬퍼 함수들
def get_time_thresholds(server_name):
    """서버별 시간 임계값을 현재 시간 기준으로 계산해서 반환"""
    from datetime import datetime, timezone
    
    config = get_config(server_name)
    now = datetime.now(timezone.utc)
    
    # 기본 시간 임계값
    time_threshold = {}
    for pack, delta in config["time_threshold"].items():
        time_threshold[pack] = now - delta
    
    # 특수 조건 시간
    one_ago = now - config["no_reaction_time"]
    
    return {
        "now": now,
        "time_threshold": time_threshold,
        "one_ago": one_ago,  # 특수 조건용 (반응 없음, ❓만 있음)
        "bad_delete_threshold": now - config["bad_delete_time"]
    }

def get_bad_thresholds(server_name):
    """서버별 👎 반응 임계값 반환"""
    config = get_config(server_name)
    return config["bad_threshold"]

def get_special_conditions(server_name):
    """서버별 특수 조건 반환"""
    config = get_config(server_name)
    return {
        "min_question_count": config["min_question_count"],
        "no_reaction_time": config["no_reaction_time"],
        "only_question_time": config["only_question_time"]
    }