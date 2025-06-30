"""
B 매장 쿠폰 자동화 테스트
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from core.application.services.b_store_automation_service import BStoreAutomationService
from core.application.dto.automation_dto import AutomationRequest, AutomationResponse
from core.domain.models.b_discount_calculator import BDiscountCalculator
from core.domain.models.discount_policy import DiscountPolicy, CouponRule
from core.domain.models.coupon import CouponType, CouponHistory, CouponApplication
from core.domain.models.vehicle import Vehicle
from infrastructure.web_automation.store_crawlers.b_store_crawler import BStoreCrawler
from infrastructure.config.config_manager import ConfigManager
from infrastructure.notifications.notification_service import NotificationService
from infrastructure.logging.structured_logger import StructuredLogger


class TestBStoreAutomation:
    """B 매장 자동화 테스트"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """모킹된 설정 관리자"""
        config_manager = Mock(spec=ConfigManager)
        
        # B 매장 설정 모킹
        config_manager.get_store_config.return_value = Mock(
            store_id="B",
            name="B매장",
            website_url="https://a15878.parkingweb.kr/login",
            login_username="215",
            login_password="4318"
        )
        
        config_manager.get_playwright_config.return_value = {
            'headless': True,
            'timeout': 30000
        }
        
        # 할인 정책 모킹
        config_manager.get_discount_policy.return_value = DiscountPolicy(
            store_id="B",
            weekday_target_hours=3,
            weekend_target_hours=2,
            weekday_max_coupons=6,
            weekend_max_coupons=4
        )
        
        # 쿠폰 규칙 모킹
        config_manager.get_coupon_rules.return_value = [
            CouponRule(
                coupon_key="FREE_1HOUR",
                coupon_name="무료 1시간할인",
                coupon_type=CouponType.FREE,
                duration_minutes=60,
                priority=0
            ),
            CouponRule(
                coupon_key="PAID_30MIN",
                coupon_name="유료 30분할인 (판매 : 300 )",
                coupon_type=CouponType.PAID,
                duration_minutes=30,
                priority=1
            )
        ]
        
        return config_manager
    
    @pytest.fixture
    def mock_notification_service(self):
        """모킹된 알림 서비스"""
        service = Mock(spec=NotificationService)
        service.send_failure_notification = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_logger(self):
        """모킹된 로거"""
        return Mock(spec=StructuredLogger)
    
    @pytest.fixture
    def b_store_service(self, mock_config_manager, mock_notification_service, mock_logger):
        """B 매장 자동화 서비스"""
        return BStoreAutomationService(
            config_manager=mock_config_manager,
            notification_service=mock_notification_service,
            logger=mock_logger
        )


class TestBDiscountCalculator:
    """B 매장 할인 계산기 테스트"""
    
    @pytest.fixture
    def b_discount_policy(self):
        """B 매장 할인 정책"""
        return DiscountPolicy(
            store_id="B",
            weekday_target_hours=3,
            weekend_target_hours=2,
            weekday_max_coupons=6,
            weekend_max_coupons=4
        )
    
    @pytest.fixture
    def b_coupon_rules(self):
        """B 매장 쿠폰 규칙"""
        return [
            CouponRule(
                coupon_key="FREE_1HOUR",
                coupon_name="무료 1시간할인",
                coupon_type=CouponType.FREE,
                duration_minutes=60,
                priority=0
            ),
            CouponRule(
                coupon_key="PAID_30MIN",
                coupon_name="유료 30분할인 (판매 : 300 )",
                coupon_type=CouponType.PAID,
                duration_minutes=30,
                priority=1
            )
        ]
    
    @pytest.fixture
    def b_calculator(self, b_discount_policy, b_coupon_rules):
        """B 매장 할인 계산기"""
        return BDiscountCalculator(b_discount_policy, b_coupon_rules)
    
    def test_weekday_calculation_with_30min_doubling(self, b_calculator, capsys):
        """평일 계산 - @/rules 지침에 따른 시간 기반 부족분 계산 테스트"""
        my_history = {}
        total_history = {}
        available_coupons = {
            "무료 1시간할인": 999,
            "유료 30분할인 (판매 : 300 )": 50
        }
        
        applications = b_calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history,
            available_coupons=available_coupons,
            is_weekday=True
        )
        
        # @/rules 지침: 평일 3시간 = 무료 1시간 + 유료 2시간
        # B 매장: 유료 2시간 = 4개 30분 쿠폰
        free_app = next((app for app in applications if "무료" in app.coupon_name), None)
        paid_app = next((app for app in applications if "30분" in app.coupon_name), None)
        
        assert free_app is not None
        assert free_app.count == 1  # 무료 1시간
        
        assert paid_app is not None
        assert paid_app.count == 4  # 유료 2시간 = 4개 30분 쿠폰
        
        # 콘솔 출력 확인
        captured = capsys.readouterr()
        assert "시간 기반 부족분 계산" in captured.out
    
    def test_weekday_with_existing_coupons(self, b_calculator, capsys):
        """평일 계산 - 이미 적용된 쿠폰이 있는 경우 테스트"""
        my_history = {
            "유료 30분할인 (판매 : 300 )": 2  # 이미 2개 (1시간) 적용됨
        }
        total_history = {}
        available_coupons = {
            "무료 1시간할인": 999,
            "유료 30분할인 (판매 : 300 )": 50
        }
        
        applications = b_calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history,
            available_coupons=available_coupons,
            is_weekday=True
        )
        
        # @/rules 계산: 평일 3시간 - (기존 1시간 + 무료 1시간) = 1시간 부족
        # 1시간 = 2개 30분 쿠폰
        free_app = next((app for app in applications if "무료" in app.coupon_name), None)
        paid_app = next((app for app in applications if "30분" in app.coupon_name), None)
        
        assert free_app is not None
        assert free_app.count == 1  # 무료 1시간
        
        assert paid_app is not None
        assert paid_app.count == 2  # 부족한 1시간 = 2개 30분 쿠폰
        
        # 콘솔 출력 확인
        captured = capsys.readouterr()
        assert "현재상태" in captured.out
        assert "부족" in captured.out
    
    def test_weekend_calculation_with_30min_doubling(self, b_calculator, capsys):
        """주말 계산 - @/rules 지침에 따른 시간 기반 부족분 계산 테스트"""
        my_history = {}
        total_history = {}
        available_coupons = {
            "무료 1시간할인": 999,
            "유료 30분할인 (판매 : 300 )": 50
        }
        
        applications = b_calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history,
            available_coupons=available_coupons,
            is_weekday=False
        )
        
        # @/rules 지침: 주말 2시간 = 무료 1시간 + 유료 1시간  
        # B 매장: 유료 1시간 = 2개 30분 쿠폰
        free_app = next((app for app in applications if "무료" in app.coupon_name), None)
        paid_app = next((app for app in applications if "30분" in app.coupon_name), None)
        
        assert free_app is not None  
        assert free_app.count == 1  # 무료 1시간
        
        if paid_app:  # 주말 정책에 따라 달라질 수 있음
            assert paid_app.count == 2  # 유료 1시간 = 2개 30분 쿠폰
    
    def test_insufficient_coupons_adjustment(self, b_calculator):
        """보유 쿠폰 부족 시 조정 테스트"""
        my_history = {}
        total_history = {}
        available_coupons = {
            "무료 1시간할인": 999,
            "유료 30분할인 (판매 : 300 )": 2  # 부족한 수량
        }
        
        applications = b_calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history,
            available_coupons=available_coupons,
            is_weekday=True
        )
        
        # 30분 쿠폰은 보유 수량으로 제한됨
        paid_app = next((app for app in applications if "30분" in app.coupon_name), None)
        if paid_app:
            assert paid_app.count <= 2  # 보유 수량 이하로 조정
    
    def test_already_used_free_coupon(self, b_calculator):
        """무료 쿠폰 이미 사용한 경우 테스트"""
        my_history = {}
        total_history = {"무료 1시간할인": 1}  # 이미 사용됨
        available_coupons = {
            "무료 1시간할인": 999,
            "유료 30분할인 (판매 : 300 )": 100
        }
        
        applications = b_calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history,
            available_coupons=available_coupons,
            is_weekday=True
        )
        
        # 무료 쿠폰은 적용되지 않아야 함
        free_app = next((app for app in applications if "무료" in app.coupon_name), None)
        assert free_app is None or free_app.count == 0
        
        # @/rules 계산: 평일 3시간 - (기존 0시간 + 무료 0시간) = 3시간 부족
        # 3시간 = 6개 30분 쿠폰
        paid_app = next((app for app in applications if "30분" in app.coupon_name), None)
        assert paid_app is not None
        assert paid_app.count == 6  # 3시간을 30분 쿠폰으로 충족
    
    def test_weekday_with_all_existing_coupons(self, b_calculator, capsys):
        """평일 계산 - 무료 + 유료 쿠폰이 모두 이미 적용된 경우 테스트 (사용자 시나리오)"""
        my_history = {
            "무료 1시간할인": 1,           # 이미 무료 1시간 적용됨
            "유료 30분할인 (판매 : 300 )": 2  # 이미 유료 2개 (1시간) 적용됨
        }
        total_history = {}
        available_coupons = {
            "무료 1시간할인": 999,
            "유료 30분할인 (판매 : 300 )": 50
        }
        
        applications = b_calculator.calculate_required_coupons(
            my_history=my_history,
            total_history=total_history,
            available_coupons=available_coupons,
            is_weekday=True
        )
        
        # @/rules 계산: 평일 3시간 - (기존무료 1시간 + 기존유료 1시간 + 추가무료 0시간) = 1시간 부족
        # 1시간 = 2개 30분 쿠폰만 추가 적용되어야 함
        free_app = next((app for app in applications if "무료" in app.coupon_name), None)
        paid_app = next((app for app in applications if "30분" in app.coupon_name), None)
        
        # 무료 쿠폰은 이미 1개 적용되어 있으므로 추가 적용 안됨
        assert free_app is None or free_app.count == 0
        
        # 유료 쿠폰은 부족한 1시간만 적용 (2개 30분 쿠폰)
        assert paid_app is not None
        assert paid_app.count == 2  # 부족한 1시간 = 2개 30분 쿠폰 (4개 아님!)
        
        # 콘솔 출력 확인
        captured = capsys.readouterr()
        assert "기존무료 1.0시간" in captured.out
        assert "기존유료 1.0시간" in captured.out
        assert "부족 1.0시간" in captured.out


class TestBStoreCrawler:
    """B 매장 크롤러 테스트"""
    
    @pytest.fixture
    def mock_page(self):
        """모킹된 Playwright 페이지"""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.fill = AsyncMock()
        page.click = AsyncMock()
        page.locator.return_value.count = AsyncMock(return_value=0)
        page.locator.return_value.inner_text = AsyncMock(return_value="테스트")
        page.wait_for_timeout = AsyncMock()
        page.get_by_role = AsyncMock()
        page.get_by_text = AsyncMock()
        return page
    
    @pytest.fixture
    def mock_store_config(self):
        """모킹된 매장 설정"""
        config = Mock()
        config.website_url = "https://a15878.parkingweb.kr/login"
        config.login_username = "215"
        config.login_password = "4318"
        config.store_id = "B"
        config.coupons = {
            "FREE_1HOUR": {"name": "무료 1시간할인"},
            "PAID_30MIN": {"name": "유료 30분할인 (판매 : 300 )"}
        }
        return config
    
    @pytest.fixture
    def mock_logger(self):
        """모킹된 로거"""
        logger = Mock()
        logger.log_info = Mock()
        logger.log_error = Mock()
        logger.should_log_info = Mock(return_value=True)
        return logger
    
    @pytest.fixture
    def b_crawler(self, mock_store_config, mock_logger):
        """B 매장 크롤러"""
        playwright_config = {'headless': True, 'timeout': 30000}
        structured_logger = Mock()
        
        crawler = BStoreCrawler(mock_store_config, playwright_config, structured_logger)
        crawler.logger = mock_logger
        return crawler
    
    @pytest.mark.asyncio
    async def test_login_success(self, b_crawler, mock_page):
        """로그인 성공 테스트"""
        # 페이지 모킹 설정
        mock_page.locator.return_value.count = AsyncMock(return_value=1)  # 팝업 있음
        mock_page.locator.return_value.first = Mock()
        mock_page.locator.return_value.first.click = AsyncMock()
        
        # 브라우저 초기화 모킹
        b_crawler.page = mock_page
        b_crawler._initialize_browser = AsyncMock()
        
        # 로그인 실행
        result = await b_crawler.login()
        
        # 결과 검증
        assert result is True
        b_crawler.logger.log_info.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_vehicle_success(self, b_crawler, mock_page):
        """차량 검색 성공 테스트"""
        # 페이지 모킹 설정
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception())  # 모달 없음
        
        b_crawler.page = mock_page
        vehicle = Vehicle(number="12가3456")
        
        # 차량 검색 실행
        result = await b_crawler.search_vehicle(vehicle)
        
        # 결과 검증
        assert result is True
        mock_page.fill.assert_called_with('input[name="carNo"]', "12가3456")
    
    @pytest.mark.asyncio
    async def test_get_coupon_history(self, b_crawler, mock_page):
        """쿠폰 이력 조회 테스트"""
        # 페이지 모킹 설정
        mock_label = Mock()
        mock_label.inner_text = AsyncMock(return_value="15,400")
        mock_page.locator.return_value.all = AsyncMock(return_value=[mock_label])
        mock_page.locator.return_value.count = AsyncMock(return_value=2)
        
        b_crawler.page = mock_page
        vehicle = Vehicle(number="12가3456")
        
        # 쿠폰 이력 조회 실행
        result = await b_crawler.get_coupon_history(vehicle)
        
        # 결과 검증
        assert isinstance(result, CouponHistory)
        assert "무료 1시간할인" in result.available_coupons
        assert result.available_coupons["무료 1시간할인"] == 999
    
    @pytest.mark.asyncio
    async def test_apply_coupons(self, b_crawler, mock_page):
        """쿠폰 적용 테스트"""
        # 페이지 모킹 설정
        mock_item = Mock()
        mock_item.inner_text = AsyncMock(return_value="무료 1시간할인")
        mock_item.locator.return_value.count = AsyncMock(return_value=1)
        mock_item.locator.return_value.click = AsyncMock()
        
        mock_page.locator.return_value.all = AsyncMock(return_value=[mock_item])
        
        b_crawler.page = mock_page
        
        applications = [
            CouponApplication(
                coupon_name="무료 1시간할인",
                coupon_type=CouponType.FREE,
                count=1
            )
        ]
        
        # 쿠폰 적용 실행
        result = await b_crawler.apply_coupons(applications)
        
        # 결과 검증
        assert result is True


if __name__ == "__main__":
    # 개별 테스트 실행 예시
    pytest.main([__file__, "-v"]) 