"""
B 매장 자동화 테스트 - 로그를 실시간으로 볼 수 있도록 실행
차량번호: 9335, headless=false
"""
import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.application.dto.automation_dto import AutomationRequest
from infrastructure.config.config_manager import ConfigManager
from infrastructure.factories.automation_factory import AutomationFactory

# 콘솔 로깅 설정 (실시간 출력)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 콘솔 출력
        logging.FileHandler(f'b_store_real_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)

async def main():
    """B 매장 실제 자동화 테스트 실행 (로그 실시간 출력)"""
    print("="*80)
    print("🅱️  B 매장 자동화 테스트 (로그 실시간 출력)")
    print("="*80)
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🚗 차량번호: 2811")
    print(f"🖥️  브라우저 모드: headless=false (화면 표시)")
    print(f"🔄 실행 방식: 실제 Lambda 핸들러 플로우")
    print("="*80)
    
    try:
        # 설정 관리자 및 팩토리 초기화
        print("\n🔧 [초기화] 설정 및 팩토리 초기화 중...")
        config_manager = ConfigManager()
        factory = AutomationFactory(config_manager)
        
        # 자동화 요청 생성
        request = AutomationRequest(
            store_id="B",
            vehicle_number="2811"
        )
        
        print(f"\n🚀 [시작] B 매장 자동화 시작")
        print(f"   - 매장 ID: {request.store_id}")
        print(f"   - 차량번호: {request.vehicle_number}")
        print(f"   - 요청 ID: {request.request_id}")
        
        # 유스케이스 실행
        print(f"\n⚙️  [실행] 자동화 프로세스 시작...")
        print("   (아래부터 실시간 로그 출력)")
        print("-" * 80)
        
        use_case = factory.create_apply_coupon_use_case(request.store_id)
        response = await use_case.execute(request)
        
        print("-" * 80)
        print(f"✅ [완료] 자동화 프로세스 완료")
        
        # 결과 출력
        print(f"\n📊 [결과] 자동화 실행 결과:")
        print(f"   - 성공 여부: {'✅ 성공' if response.success else '❌ 실패'}")
        print(f"   - 요청 ID: {response.request_id}")
        print(f"   - 매장 ID: {response.store_id}")
        print(f"   - 차량번호: {response.vehicle_number}")
        print(f"   - 완료 시간: {response.completed_at}")
        
        if response.success:
            if response.applied_coupons:
                print(f"\n🎫 [쿠폰] 적용된 쿠폰 내역:")
                total_count = 0
                for coupon_info in response.applied_coupons:
                    for name, count in coupon_info.items():
                        print(f"   - {name}: {count}개")
                        total_count += count
                print(f"   📊 총 적용 개수: {total_count}개")
            else:
                print(f"\n ℹ️ [정보] 적용할 쿠폰이 없었습니다.")
                
            # 성공 결과를 JSON 파일로 저장
            import json
            result_data = {
                "success": response.success,
                "request_id": response.request_id,
                "store_id": response.store_id,
                "vehicle_number": response.vehicle_number,
                "applied_coupons": response.applied_coupons,
                "completed_at": response.completed_at.isoformat() if response.completed_at else None,
                "error_message": response.error_message
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = f"b_store_result_{timestamp}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            print(f"\n📄 [저장] 결과가 '{result_file}'에 저장되었습니다.")
            
        else:
            print(f"\n❌ [오류] 자동화 실패!")
            print(f"   - 오류 메시지: {response.error_message}")
            return False
            
    except KeyboardInterrupt:
        print(f"\n⏹️  [중단] 사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n💥 [예외] 테스트 실행 중 예외 발생:")
        print(f"   - 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n🎉 [완료] B 매장 자동화 테스트 완료!")
    print("="*80)
    return True

if __name__ == "__main__":
    asyncio.run(main()) 