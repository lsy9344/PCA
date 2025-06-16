"""
할인 정책 도메인 모델
"""
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
from .coupon import CouponApplication, CouponType


@dataclass
class DiscountPolicy:
    """할인 정책"""
    store_id: str
    weekday_target_hours: int = 3
    weekend_target_hours: int = 2
    weekday_max_coupons: int = 5
    weekend_max_coupons: int = 3
    
    def get_target_hours(self, is_weekday: bool) -> int:
        """목표 할인 시간 조회"""
        return self.weekday_target_hours if is_weekday else self.weekend_target_hours
    
    def get_max_coupons(self, is_weekday: bool) -> int:
        """최대 쿠폰 개수 조회"""
        return self.weekday_max_coupons if is_weekday else self.weekend_max_coupons


@dataclass
class CouponRule:
    """쿠폰 규칙"""
    coupon_key: str
    coupon_name: str
    coupon_type: CouponType
    duration_minutes: int
    priority: int = 0  # 우선순위 (낮을수록 우선)
    
    def get_duration_hours(self) -> float:
        """시간 단위로 변환"""
        return self.duration_minutes / 60.0


class DiscountCalculator:
    """할인 계산기"""
    
    def __init__(self, policy: DiscountPolicy, coupon_rules: List[CouponRule]):
        self.policy = policy
        self.coupon_rules = sorted(coupon_rules, key=lambda x: x.priority)
    
    def calculate_required_coupons(self, 
                                 my_history: Dict[str, int],
                                 total_history: Dict[str, int],
                                 available_coupons: Dict[str, int],
                                 is_weekday: bool) -> List[CouponApplication]:
        """필요한 쿠폰 계산"""
        target_hours = self.policy.get_target_hours(is_weekday)
        max_coupons = self.policy.get_max_coupons(is_weekday)
        
        applications = []
        remaining_hours = target_hours
        total_coupon_count = 0
        
        # 무료 쿠폰 우선 적용 (전체 이력에서 사용하지 않은 경우)
        free_rules = [rule for rule in self.coupon_rules if rule.coupon_type == CouponType.FREE]
        for rule in free_rules:
            if remaining_hours <= 0 or total_coupon_count >= max_coupons:
                break
                
            # 전체 매장에서 이미 사용했다면 스킵
            if total_history.get(rule.coupon_name, 0) > 0:
                continue
            
            # 내 매장에서 이미 사용한 개수 확인
            my_used = my_history.get(rule.coupon_name, 0)
            available = available_coupons.get(rule.coupon_name, 0)
            
            # 적용 가능한 개수 계산
            needed_hours = min(remaining_hours, rule.get_duration_hours())
            needed_count = min(1, available - my_used)  # 무료는 보통 1개만
            
            if needed_count > 0 and total_coupon_count + needed_count <= max_coupons:
                applications.append(CouponApplication(
                    coupon_name=rule.coupon_name,
                    coupon_type=rule.coupon_type,
                    count=needed_count
                ))
                remaining_hours -= needed_hours
                total_coupon_count += needed_count
        
        # 유료/주말 쿠폰으로 나머지 시간 채우기
        paid_rules = [rule for rule in self.coupon_rules 
                     if rule.coupon_type in [CouponType.PAID, CouponType.WEEKEND]]
        
        for rule in paid_rules:
            if remaining_hours <= 0 or total_coupon_count >= max_coupons:
                break
            
            # 주말 쿠폰은 주말에만, 평일 쿠폰은 평일에만
            if rule.coupon_type == CouponType.WEEKEND and is_weekday:
                continue
            
            my_used = my_history.get(rule.coupon_name, 0)
            available = available_coupons.get(rule.coupon_name, 0)
            
            # 필요한 개수 계산
            needed_count = min(
                int(remaining_hours / rule.get_duration_hours()) + (1 if remaining_hours % rule.get_duration_hours() > 0 else 0),
                available - my_used,
                max_coupons - total_coupon_count
            )
            
            if needed_count > 0:
                applications.append(CouponApplication(
                    coupon_name=rule.coupon_name,
                    coupon_type=rule.coupon_type,
                    count=needed_count
                ))
                remaining_hours -= needed_count * rule.get_duration_hours()
                total_coupon_count += needed_count
        
        return [app for app in applications if app.is_valid()] 