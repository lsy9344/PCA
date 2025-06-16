"""
기본 웹 크롤러
"""
from abc import ABC
from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, Any, Optional

from core.domain.repositories.store_repository import StoreRepository
from core.domain.models.store import StoreConfig
from infrastructure.logging.structured_logger import StructuredLogger


class BaseCrawler(StoreRepository, ABC):
    """기본 웹 크롤러"""
    
    def __init__(self, 
                 store_config: StoreConfig,
                 playwright_config: Dict[str, Any],
                 logger: StructuredLogger):
        self.store_config = store_config
        self.playwright_config = playwright_config
        self.logger = logger
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def _initialize_browser(self) -> None:
        """브라우저 초기화"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.playwright_config.get('headless', True)
            )
            self.page = await self.browser.new_page()
            
            # 기본 타임아웃 설정
            self.page.set_default_timeout(self.playwright_config.get('timeout', 30000))
    
    async def cleanup(self) -> None:
        """리소스 정리"""
        try:
            # 페이지 정리
            if self.page:
                try:
                    await self.page.close()
                    self.logger.debug("페이지 정리 완료")
                except Exception:
                    pass
                finally:
                    self.page = None
            
            # 브라우저 정리
            if self.browser:
                try:
                    await self.browser.close()
                    self.logger.debug("브라우저 정리 완료")
                except Exception:
                    pass
                finally:
                    self.browser = None
            
            # Playwright 정리
            if self.playwright:
                try:
                    await self.playwright.stop()
                    self.logger.debug("Playwright 정리 완료")
                except Exception:
                    pass
                finally:
                    self.playwright = None
                    
        except Exception as e:
            self.logger.warning(f"리소스 정리 중 오류: {str(e)}")
    
    async def _safe_click(self, selector: str, timeout: int = 5000) -> bool:
        """안전한 클릭 (에러 시 False 반환)"""
        try:
            await self.page.click(selector, timeout=timeout)
            return True
        except Exception as e:
            self.logger.debug(f"클릭 실패 ({selector}): {str(e)}")
            return False
    
    async def _safe_fill(self, selector: str, value: str, timeout: int = 5000) -> bool:
        """안전한 입력 (에러 시 False 반환)"""
        try:
            await self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception as e:
            self.logger.debug(f"입력 실패 ({selector}): {str(e)}")
            return False
    
    async def _safe_wait_for_selector(self, selector: str, timeout: int = 5000) -> bool:
        """안전한 셀렉터 대기 (에러 시 False 반환)"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            self.logger.debug(f"셀렉터 대기 실패 ({selector}): {str(e)}")
            return False
    
    async def _try_multiple_selectors(self, selectors: list[str], action: str = "click") -> bool:
        """여러 셀렉터 시도"""
        for selector in selectors:
            try:
                if action == "click":
                    if await self._safe_click(selector):
                        return True
                elif action == "wait":
                    if await self._safe_wait_for_selector(selector):
                        return True
            except Exception:
                continue
        return False 