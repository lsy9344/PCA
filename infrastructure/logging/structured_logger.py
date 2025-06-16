"""
구조화된 로거
"""
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogger:
    """구조화된 로깅을 위한 로거"""
    
    def __init__(self, name: str, log_config: Dict[str, Any]):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        # 기존 핸들러 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 파일 핸들러 설정
        log_dir = Path(log_config['log_dir'])
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{name}.log",
            maxBytes=log_config['max_file_size'],
            backupCount=log_config['backup_count'],
            encoding='utf-8'
        )
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        
        # 포매터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _format_message(self, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """메시지 포맷팅"""
        if extra:
            # 구조화된 데이터를 JSON으로 추가
            structured_data = json.dumps(extra, ensure_ascii=False, default=str)
            return f"{message} | {structured_data}"
        return message
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """정보 로그"""
        formatted_message = self._format_message(message, extra)
        self.logger.info(formatted_message)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """경고 로그"""
        formatted_message = self._format_message(message, extra)
        self.logger.warning(formatted_message)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """에러 로그"""
        formatted_message = self._format_message(message, extra)
        self.logger.error(formatted_message)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """디버그 로그"""
        formatted_message = self._format_message(message, extra)
        self.logger.debug(formatted_message) 