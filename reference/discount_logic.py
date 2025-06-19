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
    is_weekday: bool,
    coupon_durations: Dict[str, int] = None
) -> Dict[str, int]:
    """
    적용할 쿠폰 개수 결정 (시간 기반 계산)
    
    Args:
        my_history: 매장별 할인권 사용 이력 (쿠폰명→사용횟수)
        total_history: 전체 무료 쿠폰 사용 이력 (쿠폰명→사용횟수)
        discount_types: 쿠폰 타입 정의
        is_weekday: 평일 여부
        coupon_durations: 쿠폰별 지속시간(분) 정의
    
    Returns:
        Dict[str, int]: 적용할 쿠폰 개수
    """
    free_key = discount_types['FREE_1HOUR']
    paid_key = discount_types['PAID_1HOUR']
    weekend_key = discount_types['WEEKEND_1HOUR']

    # 기본 쿠폰 지속시간 (분) - A매장 기준
    if coupon_durations is None:
        coupon_durations = {
            free_key: 60,    # 30분할인권(무료) -> 실제로는 60분
            paid_key: 60,    # 1시간할인권(유료)
            weekend_key: 60  # 1시간주말할인권(유료)
        }

    total_free_used = total_history.get(free_key, 0)
    my_free = my_history.get(free_key, 0)
    my_paid = my_history.get(paid_key, 0)
    my_weekend = my_history.get(weekend_key, 0)

    # 현재 적용된 총 시간 계산 (분 단위)
    current_minutes = (
        my_free * coupon_durations[free_key] +
        my_paid * coupon_durations[paid_key] +
        my_weekend * coupon_durations[weekend_key]
    )
    current_hours = current_minutes / 60.0

    if is_weekday:
        target_hours = 3.0
        remaining_hours = max(0, target_hours - current_hours)
        
        # 무료 쿠폰 적용 여부 결정
        free_apply = 0 if total_free_used > 0 else max(0, 1 - my_free)
        
        # 무료 쿠폰 적용 시 추가되는 시간 계산
        free_hours_to_add = free_apply * (coupon_durations[free_key] / 60.0)
        
        # 유료 쿠폰으로 채워야 할 시간
        paid_hours_needed = max(0, remaining_hours - free_hours_to_add)
        
        # 필요한 유료 쿠폰 개수 (올림 처리)
        paid_apply = 0
        if paid_hours_needed > 0:
            paid_apply = int((paid_hours_needed * 60 + coupon_durations[paid_key] - 1) // coupon_durations[paid_key])
        
        result = {
            free_key: free_apply,
            paid_key: paid_apply,
            weekend_key: 0
        }
    else:
        target_hours = 2.0
        remaining_hours = max(0, target_hours - current_hours)
        
        # 무료 쿠폰 적용 여부 결정
        free_apply = 0 if total_free_used > 0 else max(0, 1 - my_free)
        
        # 무료 쿠폰 적용 시 추가되는 시간 계산
        free_hours_to_add = free_apply * (coupon_durations[free_key] / 60.0)
        
        # 주말 쿠폰으로 채워야 할 시간
        weekend_hours_needed = max(0, remaining_hours - free_hours_to_add)
        
        # 필요한 주말 쿠폰 개수 (올림 처리)
        weekend_apply = 0
        if weekend_hours_needed > 0:
            weekend_apply = int((weekend_hours_needed * 60 + coupon_durations[weekend_key] - 1) // coupon_durations[weekend_key])
        
        result = {
            free_key: free_apply,
            paid_key: 0,
            weekend_key: weekend_apply
        }

    # 적용할 쿠폰 결과 로깅
    logger.info(">>>>>[적용할 쿠폰]<<<<<")
    logger.info(f"현재 적용된 시간: {current_hours:.1f}시간")
    logger.info(f"목표 시간: {target_hours:.1f}시간")
    logger.info(f"남은 필요 시간: {remaining_hours:.1f}시간")
    for name, count in result.items():
        if count > 0:
            logger.info(f"{name}: {count}개")
    
    return result 