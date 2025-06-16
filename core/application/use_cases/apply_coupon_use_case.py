"""
쿠폰 적용 유스케이스
"""
from datetime import datetime
from typing import List
import traceback

from ..dto.automation_dto import AutomationRequest, AutomationResponse, ErrorContext
from core.domain.models.vehicle import Vehicle
from core.domain.models.discount_policy import DiscountCalculator
from core.domain.repositories.store_repository import StoreRepository
from infrastructure.notifications.notification_service import NotificationService
from infrastructure.logging.structured_logger import StructuredLogger
from shared.utils.date_utils import DateUtils


class ApplyCouponUseCase:
    """쿠폰 적용 유스케이스"""
    
    def __init__(self,
                 store_repository: StoreRepository,
                 discount_calculator: DiscountCalculator,
                 notification_service: NotificationService,
                 logger: StructuredLogger):
        self._store_repository = store_repository
        self._discount_calculator = discount_calculator
        self._notification_service = notification_service
        self._logger = logger
    
    async def execute(self, request: AutomationRequest) -> AutomationResponse:
        """쿠폰 적용 실행"""
        vehicle = Vehicle(number=request.vehicle_number)
        
        try:
            self._logger.info(
                f"[{request.store_id}] 쿠폰 자동화 시작",
                extra={"store_id": request.store_id, "vehicle": request.vehicle_number}
            )
            
            # 1. 로그인
            if not await self._store_repository.login():
                raise Exception("로그인 실패")
            
            self._logger.info(f"[{request.store_id}][로그인] 성공")
            
            # 2. 차량 검색
            if not await self._store_repository.search_vehicle(vehicle):
                raise Exception("차량 검색 실패")
            
            self._logger.info(f"[{request.store_id}][차량검색] 성공: {request.vehicle_number}")
            
            # 3. 쿠폰 이력 조회
            coupon_history = await self._store_repository.get_coupon_history(vehicle)
            self._logger.info(f"[{request.store_id}][쿠폰조회] 성공")
            
            # 4. 적용할 쿠폰 계산
            is_weekday = DateUtils.is_weekday(datetime.now())
            applications = self._discount_calculator.calculate_required_coupons(
                coupon_history.my_history,
                coupon_history.total_history,
                coupon_history.available_coupons,
                is_weekday
            )
            
            if not applications:
                self._logger.info(f"[{request.store_id}][쿠폰적용] 적용할 쿠폰이 없습니다")
                return AutomationResponse(
                    request_id=request.request_id,
                    success=True,
                    store_id=request.store_id,
                    vehicle_number=request.vehicle_number,
                    applied_coupons=[]
                )
            
            # 5. 쿠폰 적용
            if not await self._store_repository.apply_coupons(applications):
                raise Exception("쿠폰 적용 실패")
            
            # 적용된 쿠폰 로깅
            applied_coupons = [
                {app.coupon_name: app.count} for app in applications
            ]
            
            self._logger.info(
                f"[{request.store_id}][쿠폰적용] 성공",
                extra={"applied_coupons": applied_coupons}
            )
            
            return AutomationResponse(
                request_id=request.request_id,
                success=True,
                store_id=request.store_id,
                vehicle_number=request.vehicle_number,
                applied_coupons=applied_coupons
            )
            
        except Exception as e:
            error_context = ErrorContext(
                store_id=request.store_id,
                vehicle_number=request.vehicle_number,
                error_step=self._get_current_step(str(e)),
                error_message=str(e),
                error_time=datetime.now(),
                stack_trace=traceback.format_exc()
            )
            
            await self._handle_error(error_context)
            
            return AutomationResponse(
                request_id=request.request_id,
                success=False,
                store_id=request.store_id,
                vehicle_number=request.vehicle_number,
                applied_coupons=[],
                error_message=str(e)
            )
        
        finally:
            await self._store_repository.cleanup()
    
    def _get_current_step(self, error_message: str) -> str:
        """에러 메시지에서 현재 단계 추출"""
        if "로그인" in error_message:
            return "로그인"
        elif "차량 검색" in error_message or "검색된 차량이 없습니다" in error_message:
            return "차량검색"
        elif "쿠폰 이력" in error_message or "쿠폰조회" in error_message:
            return "쿠폰조회"
        elif "쿠폰 적용" in error_message:
            return "쿠폰적용"
        else:
            return "알 수 없음"
    
    async def _handle_error(self, error_context: ErrorContext) -> None:
        """에러 처리"""
        self._logger.error(
            f"[{error_context.store_id}] 자동화 실패: {error_context.error_message}",
            extra={
                "store_id": error_context.store_id,
                "vehicle": error_context.vehicle_number,
                "step": error_context.error_step,
                "stack_trace": error_context.stack_trace
            }
        )
        
        await self._notification_service.send_error_notification(error_context) 