# AWS Lambda 로컬 시뮬레이션 환경 설정 가이드

이 가이드는 AWS Lambda 환경을 로컬 PC에서 시뮬레이션하여 구글폼 제출 시 자동화 코드가 실행되도록 설정하는 방법을 설명합니다.

## 📋 목차

1. [환경 준비](#환경-준비)
2. [설정 파일 구성](#설정-파일-구성)
3. [로컬 서버 실행](#로컬-서버-실행)
4. [구글폼 연동](#구글폼-연동)
5. [테스트 방법](#테스트-방법)
6. [문제 해결](#문제-해결)

## 🔧 환경 준비

### 필수 소프트웨어
- Python 3.8 이상
- Git (선택사항)

### Python 패키지 설치
```bash
# 가상환경 생성 (선택사항)
python -m venv venv
venv\Scripts\activate

# 필수 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
python -m playwright install chromium
```

## ⚙️ 설정 파일 구성

### 1. 환경 설정 파일 수정

`config/environment.local` 파일을 열어서 실제 값들로 수정하세요:

```bash
# 로컬 환경 설정
ENVIRONMENT=local
DEBUG=true

# 서버 설정
LOCAL_SERVER_HOST=localhost
LOCAL_SERVER_PORT=5000

# 매장 A 설정 (실제 값으로 변경 필요)
STORE_A_URL=https://your-store-a-url.com
STORE_A_USERNAME=your_username
STORE_A_PASSWORD=your_password

# 매장 B 설정 (실제 값으로 변경 필요)
STORE_B_URL=https://your-store-b-url.com
STORE_B_USERNAME=your_username
STORE_B_PASSWORD=your_password

# 텔레그램 설정 (선택사항)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Playwright 설정
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000
```

### 2. 필수 디렉토리 생성

```bash
# 로그 디렉토리 생성
mkdir logs
```

## 🚀 로컬 서버 실행

### 방법 1: 배치 파일 사용 (권장)

1. `start_local_server.bat` 파일을 더블클릭
2. 명령 프롬프트가 열리고 서버가 시작됩니다
3. IP 주소와 웹훅 URL이 표시됩니다

### 방법 2: 직접 실행

```bash
python local_lambda_server.py
```

### 서버 실행 확인

브라우저에서 다음 URL들을 확인하세요:

- **홈페이지**: http://localhost:5000
- **테스트 페이지**: http://localhost:5000/test
- **헬스체크**: http://localhost:5000/health
- **웹훅 엔드포인트**: http://localhost:5000/webhook (POST 요청용)

## 📝 구글폼 연동

### 1. 구글폼 생성

1. 구글폼에서 새 폼 생성
2. 다음 질문들을 추가:
   - **매장 선택** (객관식): "A 매장", "B 매장"
   - **차량번호** (단답형): 텍스트 입력

### 2. Apps Script 설정

1. 구글폼에서 "더보기" → "Apps Script" 클릭
2. `google_apps_script/form_to_webhook.js` 파일의 내용을 복사하여 붙여넣기
3. 다음 설정값들을 수정:

```javascript
// 실제 PC의 IP 주소로 변경 (ipconfig로 확인)
const WEBHOOK_URL = 'http://192.168.1.100:5000/webhook';

// 텔레그램 설정 (선택사항)
const TELEGRAM_BOT_TOKEN = 'your_telegram_bot_token';
const TELEGRAM_CHAT_ID = 'your_telegram_chat_id';
```

### 3. 트리거 설정

1. Apps Script 편집기에서 "트리거" 메뉴 클릭
2. "트리거 추가" 클릭
3. 다음과 같이 설정:
   - **함수**: onFormSubmit
   - **이벤트 소스**: 스프레드시트에서
   - **이벤트 유형**: 양식 제출 시

### 4. 권한 승인

1. 트리거 저장 시 권한 요청 창이 나타남
2. "권한 검토" → "허용" 클릭

## 🧪 테스트 방법

### 1. 로컬 테스트

1. 브라우저에서 http://localhost:5000/test 접속
2. 매장과 차량번호 입력 후 "자동화 실행" 클릭
3. 결과 확인

### 2. 구글폼 테스트

1. 구글폼 링크 공유
2. 폼에 데이터 입력 후 제출
3. 로컬 서버 로그에서 요청 수신 확인
4. 자동화 실행 결과 확인

### 3. Apps Script 디버깅

1. Apps Script 편집기에서 "실행" → "checkConfiguration" 실행
2. 설정값과 연결 상태 확인
3. "실행" → "testWebhook" 실행하여 웹훅 테스트

## 🔍 PC IP 주소 확인 방법

### Windows 명령 프롬프트에서:
```cmd
ipconfig
```

### 또는 PowerShell에서:
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -eq 'Wi-Fi' -or $_.InterfaceAlias -eq 'Ethernet'}
```

일반적으로 192.168.x.x 또는 10.x.x.x 형태의 IP 주소를 사용합니다.

## 🔧 문제 해결

### 자주 발생하는 문제들

#### 1. 웹훅 서버 연결 실패
```
해결방법:
- PC 방화벽 설정 확인 (포트 5000 허용)
- 안티바이러스 소프트웨어 확인
- IP 주소가 올바른지 확인
```

#### 2. Apps Script 실행 오류
```
해결방법:
- Apps Script 권한 재승인
- 트리거 재설정
- 구글 계정 로그인 상태 확인
```

#### 3. Lambda 핸들러 import 오류
```
해결방법:
- Python 경로 설정 확인
- 필요한 모듈들이 모두 설치되었는지 확인
- 가상환경 활성화 상태 확인
```

#### 4. Playwright 브라우저 오류
```
해결방법:
- python -m playwright install chromium 재실행
- 브라우저 권한 설정 확인
- headless 모드 해제하여 디버깅
```

### 로그 확인

```bash
# 서버 로그
tail -f local_lambda_server.log

# 앱 로그 (설정에 따라)
tail -f logs/app.log
```

### 환경 설정 확인

```bash
python utils/environment.py
```

## 📞 지원

문제가 해결되지 않을 경우:

1. 로그 파일 확인
2. 환경 설정 재검토
3. 네트워크 연결 상태 확인
4. 구글폼과 Apps Script 설정 재확인

## 🚀 AWS 배포 준비

로컬 테스트가 완료되면 다음 단계로 AWS Lambda에 배포:

1. 환경 변수를 AWS Lambda 환경 변수로 설정
2. Lambda 함수 코드 패키징 및 업로드
3. API Gateway 설정
4. 구글 Apps Script의 웹훅 URL을 AWS API Gateway URL로 변경

---

이제 구글폼을 제출할 때마다 로컬 PC에서 AWS Lambda처럼 자동화 코드가 실행됩니다! 🎉 