"""
전역 설정 파일 - Playwright, Telegram 등 공통 설정을 관리
"""
from typing import Dict, Any

# Playwright 설정
PLAYWRIGHT_CONFIG = {
    "HEADLESS": False,  # 브라우저 표시 여부
    "TIMEOUT": 30000,   # 기본 타임아웃 (ms)
    "RETRY_COUNT": 2    # 재시도 횟수
}

# 텔레그램 설정
TELEGRAM_CONFIG = {
    "BOT_TOKEN": "7694000458:AAFDa7szcGRjJJUy8cU_eJnU9MPgqsWnkmk",
    "CHAT_ID": "6968094848",
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 1.0
}

# 로깅 설정
LOGGING_CONFIG = {
    "LOG_DIR": "result_logs",
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
    "BACKUP_COUNT": 5
}

# 매장별 설정
STORE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "A": {
        "WEBSITE_URL": "http://members.iparking.co.kr/#!",
        "LOGIN": {
            "USERNAME": "dtctrit2704",
            "PASSWORD": "dtctrit2704",
        },
        "DISCOUNT_TYPES": {
            "FREE_1HOUR": "30분할인권(무료)",
            "PAID_1HOUR": "1시간할인권(유료)",
            "WEEKEND_1HOUR": "1시간주말할인권(유료)"
        },
        "MAX_WEEKDAY_COUPONS": 3,  # 평일 최대 쿠폰 수
        "MAX_WEEKEND_COUPONS": 2,  # 주말 최대 쿠폰 수
    },
    "B": {
        "WEBSITE_URL": "https://a15878.parkingweb.kr/login",
        "LOGIN": {
            "USERNAME": "215",
            "PASSWORD": "4318",
        },
        "DISCOUNT_TYPES": {
            "FREE_1HOUR": "무료 1시간할인",
            "PAID_30MIN": "유료 30분할인 (판매 : 300 )"
        },
        "MAX_WEEKDAY_COUPONS": 6,  
        "MAX_WEEKEND_COUPONS": 4,  
    },
} 
