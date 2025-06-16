"""
할인권 적용 로직 - 쿠폰 적용 규칙을 구현
"""

from datetime import datetime
from typing import Dict, Any
from utils.logger import logger

def is_weekday(date: datetime) -> bool:
    """평일 여부 확인 (공휴일 제외)"""
    # TODO: 공휴일 체크 로직 추가 필요
    return date.weekday() < 5

def decide_coupon_to_apply(
    my_history: Dict[str, int],
    total_history: Dict[str, int],
    discount_types: Dict[str, str],
    is_weekday: bool
) -> Dict[str, int]:
    """
    적용할 쿠폰 개수 결정
    
    Args:
        my_history: 매장별 할인권 사용 이력 (쿠폰명→사용횟수)
        total_history: 전체 무료 쿠폰 사용 이력 (쿠폰명→사용횟수)
        discount_types: 쿠폰 타입 정의
        is_weekday: 평일 여부
    
    Returns:
        Dict[str, int]: 적용할 쿠폰 개수
    """
    free_key = discount_types['FREE_1HOUR']
    paid_key = discount_types['PAID_1HOUR']
    weekend_key = discount_types['WEEKEND_1HOUR']

    total_free_used = total_history.get(free_key, 0)
    my_free = my_history.get(free_key, 0)
    my_paid = my_history.get(paid_key, 0)
    my_weekend = my_history.get(weekend_key, 0)

    if is_weekday:
        total_needed = 3
        # 이미 적용된 시간 계산
        already_applied = my_free + my_paid
        remaining_needed = total_needed - already_applied
        
        # 무료 쿠폰 적용 여부 결정
        free_apply = 0 if total_free_used > 0 else max(0, 1 - my_free)
        
        # 남은 시간만큼 유료 쿠폰 적용
        paid_apply = max(0, remaining_needed - free_apply)
        
        result = {
            free_key: free_apply,
            paid_key: paid_apply,
            weekend_key: 0
        }
    else:
        total_needed = 2
        # 이미 적용된 시간 계산
        already_applied = my_free + my_weekend
        remaining_needed = total_needed - already_applied
        
        # 무료 쿠폰 적용 여부 결정
        free_apply = 0 if total_free_used > 0 else max(0, 1 - my_free)
        
        # 남은 시간만큼 주말 쿠폰 적용
        weekend_apply = max(0, remaining_needed - free_apply)
        
        result = {
            free_key: free_apply,
            paid_key: 0,
            weekend_key: weekend_apply
        }

    # 적용할 쿠폰 결과 로깅
    logger.info(">>>>>[적용할 쿠폰]<<<<<")
    for name, count in result.items():
        logger.info(f"{name}: {count}개")
    
    return result 