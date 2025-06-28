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
    
    # 쿠폰 타입별 목표 개수 (룰파일 4.2-4.3)
    free_coupon_target_count: int = 1  # 무료 쿠폰 목표 개수
    weekday_paid_target_count: int = 2  # 평일 유료 쿠폰 목표 개수 (2시간)
    weekend_coupon_target_count: int = 1  # 주말 쿠폰 목표 개수 (1시간)
    
    def get_target_hours(self, is_weekday: bool) -> int:
        """목표 할인 시간 조회"""
        return self.weekday_target_hours if is_weekday else self.weekend_target_hours
    
    def get_max_coupons(self, is_weekday: bool) -> int:
        """최대 쿠폰 개수 조회"""
        return self.weekday_max_coupons if is_weekday else self.weekend_max_coupons
    
    def get_coupon_target_count(self, coupon_type: CouponType, is_weekday: bool) -> int:
        """쿠폰 타입별 목표 개수 조회 (룰파일 4.2-4.3)"""
        if coupon_type == CouponType.FREE:
            return self.free_coupon_target_count
        elif coupon_type == CouponType.PAID and is_weekday:
            return self.weekday_paid_target_count
        elif coupon_type == CouponType.WEEKEND and not is_weekday:
            return self.weekend_coupon_target_count
        else:
            return 0


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
        """
        4_discount_logic.mdc 규칙에 따른 쿠폰 계산 (시간 기반)
        - 평일: 총 3시간 목표
        - 주말: 총 2시간 목표
        - 현재 적용된 시간을 계산하여 부족한 시간만 채움
        """
        applications = []
        period_type = "평일" if is_weekday else "주말"
        
        print(f"\n{'='*60}")
        print(f"[DiscountCalculator] 쿠폰 계산 시작 - {period_type}")
        print(f"{'='*60}")
        print(f"[입력데이터] 매장 쿠폰 사용이력: {my_history}")
        print(f"[입력데이터] 전체 무료쿠폰 이력: {total_history}")
        print(f"[입력데이터] 보유 쿠폰 현황: {available_coupons}")
        
        # 현재 적용된 총 시간 계산 (분 단위) - 룰파일 4.2/4.3
        current_minutes = 0
        current_detail = []
        for rule in self.coupon_rules:
            used_count = my_history.get(rule.coupon_name, 0)
            if used_count > 0:
                rule_minutes = used_count * rule.duration_minutes
                current_minutes += rule_minutes
                current_detail.append(f"{rule.coupon_name}({used_count}개×{rule.duration_minutes}분={rule_minutes}분)")
        
        current_hours = current_minutes / 60.0
        target_hours = self.policy.get_target_hours(is_weekday)
        remaining_hours = max(0, target_hours - current_hours)
        
        print(f"\n[시간계산] 현재 적용된 시간: {current_hours:.1f}시간 ({current_minutes}분)")
        if current_detail:
            print(f"[시간계산] 적용된 쿠폰 상세: {', '.join(current_detail)}")
        print(f"[시간계산] {period_type} 목표 시간: {target_hours:.1f}시간")
        print(f"[시간계산] 추가 필요 시간: {remaining_hours:.1f}시간 ({remaining_hours * 60:.0f}분)")
        
        if remaining_hours <= 0:
            print(f"\n✅ [결과] 이미 목표 시간({target_hours:.1f}시간)을 충족함. 적용할 쿠폰 없음.")
            return applications
        
        remaining_minutes = remaining_hours * 60
        
        print(f"\n{'-'*50}")
        print(f"1단계: 무료 쿠폰 계산 (룰파일 4.4)")
        print(f"{'-'*50}")
        
        # 1. 무료 쿠폰 계산 (룰파일 4.4)
        free_rules = [rule for rule in self.coupon_rules if rule.coupon_type == CouponType.FREE]
        
        if not free_rules:
            print(f"[무료쿠폰] 무료 쿠폰 규칙이 없습니다.")
        
        for rule in free_rules:
            print(f"\n[무료쿠폰] 검토 중: {rule.coupon_name}")
            
            # 무료 쿠폰 원칙: my_history 또는 total_history 중 어느 하나라도 사용되었다면 적용하지 않음
            my_used = my_history.get(rule.coupon_name, 0)
            total_used = total_history.get(rule.coupon_name, 0)
            
            print(f"[무료쿠폰] 현재 매장 사용: {my_used}개")
            print(f"[무료쿠폰] 전체 매장 사용: {total_used}개")
            
            if my_used > 0:
                print(f"[무료쿠폰] ❌ 현재 매장에서 이미 {my_used}개 사용됨. 스킵.")
                continue
                
            if total_used > 0:
                print(f"[무료쿠폰] ❌ 전체 매장에서 이미 {total_used}개 사용됨. 스킵.")
                continue
            
            # 무료 쿠폰이 한 번도 사용되지 않았다면 1개 적용
            available = available_coupons.get(rule.coupon_name, 0)
            print(f"[무료쿠폰] 보유 쿠폰: {available}개")
            print(f"[무료쿠폰] 무료 쿠폰 미사용 확인됨. 1개 적용 예정.")
            
            # 실제 적용 가능한 개수
            apply_count = min(1, available) if available > 0 else 0
            
            if apply_count > 0:
                applications.append(CouponApplication(
                    coupon_name=rule.coupon_name,
                    coupon_type=rule.coupon_type,
                    count=apply_count
                ))
                # 적용할 시간에서 차감
                apply_minutes = apply_count * rule.duration_minutes
                remaining_minutes -= apply_minutes
                
                print(f">>>>> 적용할 쿠폰: {rule.coupon_name} {apply_count}개 ({apply_minutes}분)")
                print(f"[무료쿠폰] ✅ 적용 후 남은 필요 시간: {remaining_minutes:.0f}분")
            else:
                print(f"[무료쿠폰] ❌ 보유 쿠폰 부족 (필요: 1개, 보유: {available}개)")
        
        print(f"\n{'-'*50}")
        print(f"2단계: {period_type} 쿠폰 계산 (룰파일 4.2/4.3)")
        print(f"{'-'*50}")
        
        # 2. 유료/주말 쿠폰 계산 - fallback 로직 추가
        if is_weekday:
            target_coupon_types = [CouponType.PAID]
        else:
            # 주말: 먼저 WEEKEND 타입 확인, 없으면 PAID 타입 사용
            weekend_rules = [rule for rule in self.coupon_rules if rule.coupon_type == CouponType.WEEKEND]
            if weekend_rules:
                target_coupon_types = [CouponType.WEEKEND]
                print(f"[주말쿠폰] WEEKEND 타입 쿠폰 발견: {len(weekend_rules)}개")
            else:
                target_coupon_types = [CouponType.PAID]
                print(f"[주말쿠폰] WEEKEND 타입 없음. PAID 타입으로 대체")
        
        for target_type in target_coupon_types:
            target_rules = [rule for rule in self.coupon_rules if rule.coupon_type == target_type]
            
            if not target_rules:
                print(f"[{target_type.value}쿠폰] {target_type.value} 쿠폰 규칙이 없습니다.")
                continue
            
            for rule in target_rules:
                print(f"\n[{target_type.value}쿠폰] 검토 중: {rule.coupon_name} ({rule.duration_minutes}분)")
                
                # 쿠폰별 목표 개수 기반 계산 (룰파일 4.2-4.3)
                if target_type == CouponType.PAID and not is_weekday:
                    # 주말에 PAID 쿠폰을 사용하는 경우, 주말 목표 개수 사용
                    target_count = self.policy.weekend_coupon_target_count
                    print(f"[{target_type.value}쿠폰] 주말 PAID 쿠폰 사용: 목표 {target_count}개")
                else:
                    target_count = self.policy.get_coupon_target_count(rule.coupon_type, is_weekday)
                
                my_used = my_history.get(rule.coupon_name, 0)
                additional_needed = max(0, target_count - my_used)
                available = available_coupons.get(rule.coupon_name, 0)
                
                print(f"[{target_type.value}쿠폰] 쿠폰별 목표: {target_count}개 ({target_count * rule.duration_minutes}분)")
                print(f"[{target_type.value}쿠폰] 현재 매장 사용: {my_used}개 ({my_used * rule.duration_minutes}분)")
                print(f"[{target_type.value}쿠폰] 추가 필요: {additional_needed}개 ({additional_needed * rule.duration_minutes}분)")
                print(f"[{target_type.value}쿠폰] 보유 쿠폰: {available}개")
                
                # 실제 적용 가능한 개수
                apply_count = min(additional_needed, available) if additional_needed > 0 else 0
                
                if apply_count > 0:
                    applications.append(CouponApplication(
                        coupon_name=rule.coupon_name,
                        coupon_type=rule.coupon_type,
                        count=apply_count
                    ))
                    # 적용할 시간에서 차감 (remaining_minutes 업데이트용)
                    apply_minutes = apply_count * rule.duration_minutes
                    remaining_minutes -= apply_minutes
                    
                    print(f">>>>> 적용할 쿠폰: {rule.coupon_name} {apply_count}개 ({apply_minutes}분)")
                    print(f"[{target_type.value}쿠폰] ✅ 목표 달성: {my_used + apply_count}/{target_count}개")
                else:
                    if additional_needed <= 0:
                        print(f"[{target_type.value}쿠폰] ✅ 이미 목표 달성: {my_used}/{target_count}개")
                    else:
                        print(f"[{target_type.value}쿠폰] ❌ 보유 쿠폰 부족 (필요: {additional_needed}개, 보유: {available}개)")
        
        print(f"\n{'='*60}")
        print(f"[최종결과] 적용할 쿠폰 총 {len(applications)}개")
        print(f"{'='*60}")
        
        total_apply_minutes = 0
        for app in applications:
            # 해당 쿠폰의 duration_minutes 찾기
            rule_duration = next((rule.duration_minutes for rule in self.coupon_rules 
                                if rule.coupon_name == app.coupon_name), 0)
            apply_minutes = app.count * rule_duration
            total_apply_minutes += apply_minutes
            
            print(f">>>>> 최종 적용할 쿠폰: {app.coupon_name} {app.count}개 ({apply_minutes}분)")
        
        total_apply_hours = total_apply_minutes / 60.0
        final_total_hours = current_hours + total_apply_hours
        
        print(f"\n[최종확인] 적용 전 시간: {current_hours:.1f}시간")
        print(f"[최종확인] 적용할 시간: {total_apply_hours:.1f}시간 ({total_apply_minutes}분)")
        print(f"[최종확인] 적용 후 총시간: {final_total_hours:.1f}시간")
        print(f"[최종확인] {period_type} 목표달성: {'✅ 달성' if final_total_hours >= target_hours else '❌ 미달성'}")
        print(f"{'='*60}\n")
        
        return [app for app in applications if app.is_valid()] 