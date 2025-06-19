"""
할인 정책 계산기 테스트
"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.domain.models.discount_policy import DiscountPolicy, DiscountCalculator, CouponRule
from core.domain.models.coupon import CouponType

def test_weekday_calculation():
    """평일 쿠폰 계산 테스트"""
    print("\n" + "="*60)
    print("평일 쿠폰 계산 테스트")
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
    
    # 테스트 케이스 1: 아무것도 적용되지 않은 상태
    my_history = {}
    total_history = {}
    available_coupons = {
        "30분할인권(무료)": 5,
        "1시간할인권(유료)": 10
    }
    
    result = calculator.calculate_required_coupons(
        my_history=my_history,
        total_history=total_history,
        available_coupons=available_coupons,
        is_weekday=True
    )
    
    print("테스트 케이스 1 결과:")
    for app in result:
        print(f"  - {app.coupon_name}: {app.count}개")
    
    return result

def test_weekend_calculation():
    """주말 쿠폰 계산 테스트"""
    print("\n" + "="*60)
    print("주말 쿠폰 계산 테스트")
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
            coupon_key="WEEKEND_1HOUR",
            coupon_name="1시간주말할인권(유료)",
            coupon_type=CouponType.WEEKEND,
            duration_minutes=60,
            priority=2
        )
    ]
    
    calculator = DiscountCalculator(policy, coupon_rules)
    
    # 테스트 케이스 2: 주말, 아무것도 적용되지 않은 상태
    my_history = {}
    total_history = {}
    available_coupons = {
        "30분할인권(무료)": 5,
        "1시간주말할인권(유료)": 10
    }
    
    result = calculator.calculate_required_coupons(
        my_history=my_history,
        total_history=total_history,
        available_coupons=available_coupons,
        is_weekday=False
    )
    
    print("테스트 케이스 2 결과:")
    for app in result:
        print(f"  - {app.coupon_name}: {app.count}개")
    
    return result

def test_already_applied_coupons():
    """이미 적용된 쿠폰이 있는 경우 테스트"""
    print("\n" + "="*60)
    print("이미 적용된 쿠폰이 있는 경우 테스트")
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
    
    # 테스트 케이스 3: 이미 무료 쿠폰 1개, 유료 쿠폰 1개 적용된 상태
    my_history = {
        "30분할인권(무료)": 1,
        "1시간할인권(유료)": 1
    }
    total_history = {
        "30분할인권(무료)": 1  # 전체 매장에서 무료 쿠폰 사용됨
    }
    available_coupons = {
        "30분할인권(무료)": 5,
        "1시간할인권(유료)": 10
    }
    
    result = calculator.calculate_required_coupons(
        my_history=my_history,
        total_history=total_history,
        available_coupons=available_coupons,
        is_weekday=True
    )
    
    print("테스트 케이스 3 결과:")
    for app in result:
        print(f"  - {app.coupon_name}: {app.count}개")
    
    return result

def test_insufficient_coupons():
    """보유 쿠폰이 부족한 경우 테스트"""
    print("\n" + "="*60)
    print("보유 쿠폰이 부족한 경우 테스트")
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
    
    # 테스트 케이스 4: 보유 쿠폰이 부족한 상태
    my_history = {}
    total_history = {}
    available_coupons = {
        "30분할인권(무료)": 1,
        "1시간할인권(유료)": 1  # 필요한 개수보다 적음
    }
    
    result = calculator.calculate_required_coupons(
        my_history=my_history,
        total_history=total_history,
        available_coupons=available_coupons,
        is_weekday=True
    )
    
    print("테스트 케이스 4 결과:")
    for app in result:
        print(f"  - {app.coupon_name}: {app.count}개")
    
    return result

def main():
    """메인 테스트 함수"""
    print("🔍 할인 정책 계산기 테스트")
    print("=" * 60)
    
    try:
        # 각 테스트 실행
        test_weekday_calculation()
        test_weekend_calculation()
        test_already_applied_coupons()
        test_insufficient_coupons()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트가 완료되었습니다!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 