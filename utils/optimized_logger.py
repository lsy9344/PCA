"""
AWS CloudWatch Logs 비용 최적화를 위한 로거 설정
"""
import logging
import os
from datetime import datetime
from typing import Optional

class OptimizedLogger:
    """AWS CloudWatch Logs 비용 최적화를 위한 로거 클래스"""
    
    # 에러 코드 매핑 (긴 메시지 대신 간단한 코드 사용)
    ERROR_CODES = {
        'login_failed': 'FAIL_AUTH',
        'vehicle_not_found': 'NO_VEHICLE', 
        'vehicle_search_failed': 'FAIL_SEARCH',
        'coupon_parse_failed': 'FAIL_PARSE',
        'coupon_apply_failed': 'FAIL_APPLY',
        'network_error': 'FAIL_NETWORK',
        'timeout_error': 'FAIL_TIMEOUT'
    }
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """환경별 로그 레벨 설정"""
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment == 'production':
            # 프로덕션: WARNING 레벨 이상만 기록
            self.logger.setLevel(logging.WARNING)
        elif environment == 'test':
            # 테스트: ERROR 레벨만 기록
            self.logger.setLevel(logging.ERROR)
        else:
            # 개발: INFO 레벨까지 허용
            self.logger.setLevel(logging.INFO)
        
        # 핸들러가 이미 있으면 추가하지 않음
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_error(self, store_id: str, step: str, error_code: str, details: Optional[str] = None):
        """
        간소화된 에러 로그 기록
        
        Args:
            store_id: 매장 ID (A, B, C...)
            step: 단계명 (로그인, 차량검색, 쿠폰조회, 쿠폰적용)
            error_code: 에러 코드 (ERROR_CODES 참조)
            details: 상세 정보 (텔레그램 알림용, 로그에는 기록하지 않음)
        """
        message = f"[{store_id}][{step}] {error_code}"
        self.logger.error(message)
        return details  # 텔레그램 알림에서 사용할 상세 정보 반환
    
    def log_warning(self, store_id: str, step: str, message: str):
        """경고 로그 (프로덕션에서도 기록)"""
        log_message = f"[{store_id}][{step}] {message}"
        self.logger.warning(log_message)
    
    def log_info(self, message: str):
        """정보 로그 (개발 환경에서만 기록)"""
        self.logger.info(message)
    
    def log_debug(self, message: str):
        """디버그 로그 (로컬 개발시에만 기록)"""
        self.logger.debug(message)
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return os.getenv('ENVIRONMENT') == 'production'
    
    def should_log_info(self) -> bool:
        """INFO 레벨 로그 기록 여부 확인"""
        return not self.is_production()

# 전역 로거 인스턴스
def get_optimized_logger(name: str) -> OptimizedLogger:
    """최적화된 로거 인스턴스 반환"""
    return OptimizedLogger(name)

# 기존 코드와의 호환성을 위한 래퍼 함수들
def setup_logger(name: str) -> OptimizedLogger:
    """기존 setup_logger 함수와 호환성 유지"""
    return get_optimized_logger(name) 