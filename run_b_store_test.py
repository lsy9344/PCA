"""
B 매장 자동화 테스트 실행 스크립트
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
    """B 매장 자동화 테스트 실행"""
    try:
        # 설정 관리자 및 팩토리 초기화
        config_manager = ConfigManager()
        factory = AutomationFactory(config_manager)
        
        # 자동화 요청 생성
        request = AutomationRequest(
            store_id="B",
            vehicle_number="1690"
        )
        
        print(f"[시작] B 매장 자동화 시작: 차량번호 {request.vehicle_number}")
        
        # 유스케이스 실행
        use_case = factory.create_apply_coupon_use_case(request.store_id)
        response = await use_case.execute(request)
        
        # 결과 출력
        if response.success:
            print("[성공] 자동화 성공!")
            print(f"📋 요청 ID: {response.request_id}")
            if response.applied_coupons:
                print("[쿠폰] 적용된 쿠폰:")
                for coupon_info in response.applied_coupons:
                    for name, count in coupon_info.items():
                        print(f"   - {name}: {count}개")
            else:
                print("[정보]  적용할 쿠폰이 없었습니다.")
        else:
            print("[실패] 자동화 실패!")
            print(f"[알림] 오류: {response.error_message}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"💥 예상치 못한 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 