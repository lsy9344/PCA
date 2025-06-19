"""
B 매장 수정된 로직 테스트 스크립트
- 테스트용 차량번호: 8876
- 검색 결과 없음 시 텔레그램 알림 및 프로세스 종료
- 할인등록 페이지로 이동하지 않고 현재 페이지에서만 처리
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.domain.stores.b_store import BStore
from infrastructure.config.config_manager import ConfigManager
from infrastructure.logging.structured_logger import StructuredLogger


async def test_b_store_with_8876():
    """테스트용 차량번호 8876으로 B 매장 테스트"""
    try:
        print("🚀 B 매장 수정된 로직 테스트 시작")
        print("   - 테스트용 차량번호: 8876")
        print("   - 검색 결과 없음 시 텔레그램 알림 전송 테스트")
        print("   - 할인등록 페이지 미이동 테스트")
        
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # 로거 초기화
        logger = StructuredLogger("b_store_test_8876", {})
        
        # B 매장 설정 가져오기
        store_config = config_manager.get_store_config("B")
        
        # B 매장 객체 생성
        b_store = BStore(store_config)
        
        # 테스트용 차량번호 - 실제 존재하는 차량번호로 변경
        test_vehicle_number = "347수8876"  # 앞서 테스트에서 확인한 실제 차량번호
        
        print(f"\n📋 테스트 정보:")
        print(f"   - 매장: B")
        print(f"   - 차량번호: {test_vehicle_number}")
        print(f"   - Headless 모드: False (디버깅용)")
        
        # B 매장 자동화 실행
        print(f"\n🔄 B 매장 자동화 실행 중...")
        result = await b_store.run(test_vehicle_number)
        
        # 결과 출력
        print(f"\n📊 실행 결과:")
        print(f"   - 성공 여부: {'✅ 성공' if result else '❌ 실패'}")
        
        if not result:
            print("   ℹ️ 차량번호 8876은 검색 결과가 없을 것으로 예상됩니다.")
            print("   ℹ️ 텔레그램 알림이 전송되었는지 확인하세요.")
        
        print("\n🎉 B 매장 수정된 로직 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_b_store_crawler_directly():
    """B 매장 크롤러 직접 테스트"""
    try:
        print("\n🔧 B 매장 크롤러 직접 테스트")
        
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # 로거 초기화
        logger = StructuredLogger("b_store_crawler_test", {})
        
        # B 매장 설정 가져오기
        store_config = config_manager.get_store_config("B")
        
        # B 매장 크롤러 직접 생성
        from infrastructure.web_automation.store_crawlers.b_store_crawler import BStoreCrawler
        crawler = BStoreCrawler(store_config)
        
        # Playwright 브라우저 직접 실행
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # 브라우저 화면 표시
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = await browser.new_page()
            
            try:
                # 1. 로그인 테스트
                print("\n🔐 로그인 테스트...")
                login_success = await crawler.login(page)
                if not login_success:
                    print("❌ 로그인 실패")
                    return
                print("✅ 로그인 성공")
                
                # 2. 차량 검색 테스트 (347수8876)
                print(f"\n🔍 차량 검색 테스트 (347수8876)...")
                search_success = await crawler.search_car(page, "347수8876")
                if not search_success:
                    print("ℹ️ 차량 검색 실패 (예상된 결과)")
                    print("ℹ️ 텔레그램 알림 전송 확인 필요")
                    return
                print("✅ 차량 검색 성공")
                
                # 3. 쿠폰 이력 조회 테스트 (현재 페이지에서만)
                print(f"\n📊 쿠폰 이력 조회 테스트 (현재 페이지에서만)...")
                my_history, total_history, discount_info = await crawler.get_coupon_history(page)
                print(f"   - 보유 쿠폰: {discount_info}")
                print(f"   - 우리 매장 내역: {my_history}")
                print(f"   - 전체 내역: {total_history}")
                
                print("✅ 쿠폰 이력 조회 완료")
                
            finally:
                await browser.close()
        
        print("\n🎉 B 매장 크롤러 직접 테스트 완료")
        
    except Exception as e:
        print(f"❌ 크롤러 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 함수"""
    print("=" * 60)
    print("🅱️  B 매장 수정된 로직 테스트")
    print("=" * 60)
    
    # 테스트 메뉴
    print("\n📋 테스트 메뉴:")
    print("1. B 매장 전체 테스트 (차량번호: 8876)")
    print("2. B 매장 크롤러 직접 테스트")
    print("3. 전체 테스트")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    if choice == "1":
        await test_b_store_with_8876()
    elif choice == "2":
        await test_b_store_crawler_directly()
    elif choice == "3":
        await test_b_store_crawler_directly()
        await test_b_store_with_8876()
    else:
        print("❌ 잘못된 선택입니다. 전체 테스트를 실행합니다.")
        await test_b_store_crawler_directly()
        await test_b_store_with_8876()


if __name__ == "__main__":
    asyncio.run(main()) 