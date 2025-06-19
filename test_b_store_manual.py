"""
B 매장 수동 테스트 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.application.services.b_store_automation_service import BStoreAutomationService
from core.application.dto.automation_dto import AutomationRequest
from infrastructure.config.config_manager import ConfigManager
from infrastructure.notifications.telegram_adapter import TelegramAdapter
from infrastructure.logging.structured_logger import StructuredLogger


async def test_b_store_automation():
    """B 매장 자동화 수동 테스트"""
    try:
        print("🚀 B 매장 자동화 테스트 시작")
        
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # 로거 초기화
        logger = StructuredLogger("b_store_test", {})
        
        # 텔레그램 서비스 초기화
        telegram_config = config_manager.get_telegram_config()
        notification_service = TelegramAdapter(telegram_config, logger)
        
        # B 매장 자동화 서비스 생성
        b_service = BStoreAutomationService(
            config_manager=config_manager,
            notification_service=notification_service,
            logger=logger
        )
        
        # 테스트용 차량번호 (실제 사용 시 변경 필요)
        test_vehicle_number = input("차량번호를 입력하세요 (예: 12가3456): ").strip()
        if not test_vehicle_number:
            test_vehicle_number = "12가3456"  # 기본값
        
        # 자동화 요청 생성
        request = AutomationRequest(
            store_id="B",
            vehicle_number=test_vehicle_number
        )
        
        print(f"📋 테스트 정보:")
        print(f"   - 매장: B")
        print(f"   - 차량번호: {test_vehicle_number}")
        print(f"   - Headless 모드: True")
        
        # 자동화 실행
        print("\n🔄 B 매장 자동화 실행 중...")
        response = await b_service.execute(request)
        
        # 결과 출력
        print(f"\n📊 실행 결과:")
        print(f"   - 성공 여부: {'✅ 성공' if response.success else '❌ 실패'}")
        print(f"   - 메시지: {response.message}")
        
        if response.applied_coupons:
            print(f"   - 적용된 쿠폰:")
            for coupon in response.applied_coupons:
                print(f"     • {coupon['name']}: {coupon['count']}개 ({coupon['type']})")
        else:
            print(f"   - 적용된 쿠폰: 없음")
        
        print(f"   - 실행 시간: {response.execution_time}")
        
        if not response.success and response.error_context:
            print(f"   - 에러 단계: {response.error_context.step}")
            print(f"   - 에러 상세: {response.error_context.details}")
        
        print("\n🎉 B 매장 자동화 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_b_discount_calculator():
    """B 매장 할인 계산기 단독 테스트"""
    try:
        print("\n🧮 B 매장 할인 계산기 테스트")
        
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # B 매장 할인 정책과 쿠폰 규칙 가져오기
        discount_policy = config_manager.get_discount_policy("B")
        coupon_rules = config_manager.get_coupon_rules("B")
        
        # B 매장 할인 계산기 생성
        from core.domain.models.b_discount_calculator import BDiscountCalculator
        calculator = BDiscountCalculator(discount_policy, coupon_rules)
        
        # 테스트 시나리오 1: 평일, 쿠폰 사용 이력 없음
        print("\n📋 시나리오 1: 평일, 쿠폰 사용 이력 없음")
        my_history = {}
        total_history = {}
        available_coupons = {
            "무료 1시간할인": 999,
            "유료 30분할인 (판매 : 300 )": 100
        }
        
        applications = calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history,
            available_coupons=available_coupons,
            is_weekday=True
        )
        
        print(f"✅ 계산 결과: {len(applications)}개 쿠폰")
        for app in applications:
            print(f"   - {app.coupon_name}: {app.count}개")
        
        # 테스트 시나리오 2: 무료 쿠폰 이미 사용됨
        print("\n📋 시나리오 2: 무료 쿠폰 이미 사용됨")
        total_history_used = {"무료 1시간할인": 1}
        
        applications2 = calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history_used,
            available_coupons=available_coupons,
            is_weekday=True
        )
        
        print(f"✅ 계산 결과: {len(applications2)}개 쿠폰")
        for app in applications2:
            print(f"   - {app.coupon_name}: {app.count}개")
            
    except Exception as e:
        print(f"❌ 할인 계산기 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 함수"""
    print("=" * 60)
    print("🅱️  B 매장 자동화 시스템 테스트")
    print("=" * 60)
    
    # 테스트 메뉴
    print("\n📋 테스트 메뉴:")
    print("1. B 매장 전체 자동화 테스트")
    print("2. B 매장 할인 계산기 테스트")
    print("3. 전체 테스트")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    if choice == "1":
        await test_b_store_automation()
    elif choice == "2":
        await test_b_discount_calculator()
    elif choice == "3":
        await test_b_discount_calculator()
        await test_b_store_automation()
    else:
        print("❌ 잘못된 선택입니다. 전체 테스트를 실행합니다.")
        await test_b_discount_calculator()
        await test_b_store_automation()


if __name__ == "__main__":
    asyncio.run(main()) 