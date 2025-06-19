"""
개별 컴포넌트 테스트
각 기능을 독립적으로 테스트할 수 있습니다.
"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_discount_calculator():
    """할인 계산기 단독 테스트"""
    print("🧮 할인 계산기 테스트")
    print("="*40)
    
    try:
        from core.domain.models.discount_policy import DiscountCalculator, CouponRule
        from core.domain.models.coupon import CouponType
        
        # 테스트용 쿠폰 규칙
        coupon_rules = [
            CouponRule("FREE_1HOUR", "30분할인권(무료)", CouponType.FREE, 60, 1),
            CouponRule("PAID_1HOUR", "1시간할인권(유료)", CouponType.PAID, 60, 2),
        ]
        
        calculator = DiscountCalculator(coupon_rules)
        
        # 테스트 시나리오
        test_cases = [
            {
                "name": "평일 기본 테스트",
                "my_history": {},
                "total_history": {},
                "available_coupons": {"30분할인권(무료)": 5, "1시간할인권(유료)": 10},
                "is_weekday": True
            },
            {
                "name": "주말 테스트", 
                "my_history": {},
                "total_history": {},
                "available_coupons": {"30분할인권(무료)": 5, "1시간할인권(유료)": 10},
                "is_weekday": False
            }
        ]
        
        for test_case in test_cases:
            print(f"\n📋 {test_case['name']}")
            print("-" * 30)
            
            result = calculator.calculate_required_coupons(
                test_case["my_history"],
                test_case["total_history"], 
                test_case["available_coupons"],
                test_case["is_weekday"]
            )
            
            print(f"✅ 계산 완료: {len(result)}개 쿠폰")
            for app in result:
                print(f"  - {app.coupon_name}: {app.count}개")
        
        print("\n✅ 할인 계산기 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 할인 계산기 테스트 실패: {str(e)}")
        return False

def test_environment_config():
    """환경 설정 테스트"""
    print("\n⚙️ 환경 설정 테스트")
    print("="*40)
    
    try:
        from utils.environment import load_environment_config
        
        config = load_environment_config()
        
        print("✅ 환경 설정 로드 성공")
        print(f"환경: {config.get('ENVIRONMENT', '알 수 없음')}")
        print(f"서버: {config.get('SERVER', {}).get('HOST', '알 수 없음')}:{config.get('SERVER', {}).get('PORT', '알 수 없음')}")
        
        # 매장 설정 확인
        store_a = config.get('STORE_A', {})
        if store_a.get('URL'):
            print("✅ A매장 설정 존재")
        else:
            print("⚠️ A매장 설정 누락")
            
        return True
        
    except Exception as e:
        print(f"❌ 환경 설정 테스트 실패: {str(e)}")
        return False

def test_imports():
    """모듈 import 테스트"""
    print("\n📦 모듈 Import 테스트")
    print("="*40)
    
    modules_to_test = [
        "core.domain.models.discount_policy",
        "core.domain.models.coupon", 
        "core.application.use_cases.apply_coupon_use_case",
        "interfaces.api.lambda_handler",
        "utils.environment",
    ]
    
    success_count = 0
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}: {str(e)}")
    
    print(f"\n📊 Import 결과: {success_count}/{len(modules_to_test)} 성공")
    return success_count == len(modules_to_test)

def test_data_structures():
    """데이터 구조 테스트"""
    print("\n📊 데이터 구조 테스트")
    print("="*40)
    
    try:
        from core.domain.models.coupon import CouponApplication, CouponType
        
        # CouponApplication 생성 테스트
        app = CouponApplication("테스트쿠폰", CouponType.FREE, 2)
        
        print(f"✅ CouponApplication 생성: {app.coupon_name}, {app.count}개")
        print(f"✅ 유효성 검사: {app.is_valid()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 구조 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 개별 컴포넌트 테스트")
    print("="*50)
    
    tests = [
        ("모듈 Import", test_imports),
        ("환경 설정", test_environment_config), 
        ("데이터 구조", test_data_structures),
        ("할인 계산기", test_discount_calculator),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name} 테스트 실행 중...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 테스트 통과")
        else:
            print(f"❌ {test_name} 테스트 실패")
    
    print(f"\n📊 전체 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 컴포넌트 테스트 통과!")
    else:
        print("⚠️ 일부 컴포넌트에 문제가 있습니다.") 