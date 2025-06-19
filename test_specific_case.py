"""
사용자 지적 케이스 테스트
- 시간계산: 추가 필요 시간: 1.0시간 (60분)
- 1시간할인권(유료)를 1장 더 적용해야 함
"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.domain.models.discount_policy import DiscountPolicy, DiscountCalculator, CouponRule
from core.domain.models.coupon import CouponType

def test_user_specific_case():
    """사용자가 지적한 구체적인 케이스 테스트"""
    print("\n" + "="*60)
    print("🎯 사용자 지적 케이스 테스트")
    print("상황: 이미 2시간 적용됨, 1시간 더 필요")
    print("="*60)
    
    # 테스트용 정책 설정
    policy = DiscountPolicy(
        store_id="A",
        weekday_target_hours=3,
        weekend_target_hours=2
    )
    
    # 테스트용 쿠폰 규칙
    coupon_rules = [
        CouponRule(
            coupon_key="FREE_1HOUR",
            coupon_name="30분할인권(무료)",
            coupon_type=CouponType.FREE,
            duration_minutes=60,
            priority=1
        ),
        CouponRule(
            coupon_key="PAID_1HOUR",
            coupon_name="1시간할인권(유료)",
            coupon_type=CouponType.PAID,
            duration_minutes=60,
            priority=2
        )
    ]
    
    calculator = DiscountCalculator(policy, coupon_rules)
    
    # 사용자 케이스: 이미 2시간 적용된 상태
    my_history = {
        "30분할인권(무료)": 1,  # 1개 × 60분 = 60분
        "1시간할인권(유료)": 1   # 1개 × 60분 = 60분
    }
    
    # 전체 매장에서 무료 쿠폰 이미 사용됨
    total_history = {
        "30분할인권(무료)": 1
    }
    
    # 보유 쿠폰 현황
    available_coupons = {
        "30분할인권(무료)": 0,   # 무료 쿠폰 없음
        "1시간할인권(유료)": 5    # 유료 쿠폰 5개 보유
    }
    
    # 평일 계산 실행
    result = calculator.calculate_required_coupons(
        my_history=my_history,
        total_history=total_history,
        available_coupons=available_coupons,
        is_weekday=True
    )
    
    print(f"\n🎯 예상 결과:")
    print(f"  - 현재 적용된 시간: 2.0시간")
    print(f"  - 추가 필요 시간: 1.0시간")
    print(f"  - 1시간할인권(유료) 1개 추가 적용 예상")
    
    print(f"\n✅ 실제 결과:")
    if result:
        for app in result:
            print(f"  - {app.coupon_name}: {app.count}개")
        
        # 결과 검증
        paid_coupon = next((app for app in result if "유료" in app.coupon_name), None)
        if paid_coupon and paid_coupon.count == 1:
            print(f"\n🎉 SUCCESS: 올바른 결과! 1시간할인권(유료) {paid_coupon.count}개 적용")
            return True
        else:
            print(f"\n❌ FAIL: 예상과 다른 결과")
            return False
    else:
        print(f"  - 적용할 쿠폰 없음")
        print(f"\n❌ FAIL: 쿠폰이 적용되지 않음")
        return False

if __name__ == "__main__":
    success = test_user_specific_case()
    if success:
        print(f"\n🎉 테스트 성공! 문제가 해결되었습니다.")
    else:
        print(f"\n❌ 테스트 실패! 추가 디버깅이 필요합니다.") 