@echo off
echo ========================================
echo AWS Lambda 시뮬레이션 서버 시작
echo ========================================

REM 현재 디렉토리를 스크립트가 있는 위치로 변경
cd /d "%~dp0"

REM Python 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 필요한 패키지 설치 확인
echo 필요한 Python 패키지 설치 확인 중...
pip install flask playwright

REM 브라우저 설치 (필요한 경우)
echo Playwright 브라우저 설치 확인 중...
python -m playwright install chromium

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM IP 주소 확인
echo.
echo ========================================
echo 현재 PC의 IP 주소:
ipconfig | findstr "IPv4"
echo ========================================
echo.

echo 서버 시작 중...
echo.
echo 웹훅 URL: http://localhost:5000/webhook
echo 테스트 URL: http://localhost:5000/test
echo 헬스체크: http://localhost:5000/health
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo ========================================

REM 로컬 서버 시작
python local_lambda_server.py

pause 