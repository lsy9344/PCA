"""
B 매장 전용 할인 계산기
"""
from typing import Dict, List
from .discount_policy import DiscountCalculator, DiscountPolicy, CouponRule
from .coupon import CouponApplication, CouponType


class BDiscountCalculator(DiscountCalculator):
    """B 매장 전용 할인 계산기 - 30분 쿠폰 2배 보정"""
    
    def __init__(self, policy: DiscountPolicy, coupon_rules: List[CouponRule]):
        super().__init__(policy, coupon_rules)
    
    def calculate_required_coupons(self, 
                                 my_history: Dict[str, int],
                                 total_history: Dict[str, int],
                                 available_coupons: Dict[str, int],
                                 is_weekday: bool) -> List[CouponApplication]:
        """
        B 매장 특수 규칙 적용한 쿠폰 계산
        - 기본 계산은 부모 클래스 사용
        - 30분 쿠폰에 대해서만 2배 보정 적용
        """
        period_type = "평일" if is_weekday else "주말"
        
        print(f"\n{'='*60}")
        print(f"[BDiscountCalculator] B 매장 특수 규칙 쿠폰 계산 시작 - {period_type}")
        print(f"{'='*60}")
        print(f"[입력데이터] 매장 쿠폰 사용이력: {my_history}")
        print(f"[입력데이터] 전체 무료쿠폰 이력: {total_history}")
        print(f"[입력데이터] 보유 쿠폰 현황: {available_coupons}")
        
        # 1. 부모 클래스로부터 기본 계산 수행
        base_applications = super().calculate_required_coupons(
            my_history, total_history, available_coupons, is_weekday
        )
        
        print(f"\n{'-'*50}")
        print(f"B 매장 특수 규칙 적용 (30분 쿠폰 2배 보정)")
        print(f"{'-'*50}")
        
        # 2. B 매장 특수 규칙 적용
        adjusted_applications = []
        
        for app in base_applications:
            # 해당 쿠폰의 duration_minutes 찾기
            coupon_rule = next((rule for rule in self.coupon_rules 
                              if rule.coupon_name == app.coupon_name), None)
            
            if coupon_rule and coupon_rule.duration_minutes == 30:
                # 30분 쿠폰인 경우 2배 보정
                original_count = app.count
                adjusted_count = original_count * 2
                
                print(f"[30분쿠폰] {app.coupon_name}: {original_count}개 → {adjusted_count}개 (2배 보정)")
                
                # 보유 쿠폰 개수 체크
                available = available_coupons.get(app.coupon_name, 0)
                if adjusted_count > available:
                    adjusted_count = available
                    print(f"[30분쿠폰] 보유 쿠폰 부족으로 {adjusted_count}개로 조정")
                
                adjusted_app = CouponApplication(
                    coupon_name=app.coupon_name,
                    coupon_type=app.coupon_type,
                    count=adjusted_count
                )
                adjusted_applications.append(adjusted_app)
            else:
                # 30분 쿠폰이 아닌 경우 원래 값 사용
                if coupon_rule:
                    duration = coupon_rule.duration_minutes
                    print(f"[{duration}분쿠폰] {app.coupon_name}: {app.count}개 (보정 없음)")
                adjusted_applications.append(app)
        
        print(f"\n{'='*60}")
        print(f"[B매장 최종결과] 보정 적용된 쿠폰 총 {len(adjusted_applications)}개")
        print(f"{'='*60}")
        
        for app in adjusted_applications:
            coupon_rule = next((rule for rule in self.coupon_rules 
                              if rule.coupon_name == app.coupon_name), None)
            duration = coupon_rule.duration_minutes if coupon_rule else 0
            total_minutes = app.count * duration
            
            print(f">>>>> B매장 최종: {app.coupon_name} {app.count}개 ({total_minutes}분)")
        
        print(f"{'='*60}\n")
        
        return adjusted_applications 