"""
B 매장 자동화 테스트 - 로그를 실시간으로 볼 수 있도록 실행
차량번호: 9335, headless=false
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.application.dto.automation_dto import AutomationRequest
from infrastructure.config.config_manager import ConfigManager
from infrastructure.factories.automation_factory import AutomationFactory

async def main():
    """B 매장 실제 자동화 테스트 실행 (로그 실시간 출력)"""
    try:
        # 설정 관리자 및 팩토리 초기화
        config_manager = ConfigManager()
        factory = AutomationFactory(config_manager)
        
        # 자동화 요청 생성
        request = AutomationRequest(
            store_id="B",
            vehicle_number="0280"
        )
        
        print(f"🚀 B 매장 자동화 시작 - 차량번호: {request.vehicle_number}")
        
        # 유스케이스 실행
        use_case = factory.create_apply_coupon_use_case(request.store_id)
        response = await use_case.execute(request)
        
        # 결과 출력
        if response.success:
            print(f"✅ 자동화 완료 - 매장: {response.store_id}, 차량: {response.vehicle_number}")
            
            if response.applied_coupons:
                total_count = 0
                for coupon_info in response.applied_coupons:
                    for name, count in coupon_info.items():
                        print(f"🎫 쿠폰 적용: {name} - {count}개")
                        total_count += count
                print(f"📊 총 적용 쿠폰: {total_count}개")
            else:
                print("ℹ️ 적용할 쿠폰이 없었습니다.")
            
        else:
            print(f"❌ 자동화 실패: {response.error_message}")
            return False
            
    except KeyboardInterrupt:
        print("⏹️ 사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main()) 