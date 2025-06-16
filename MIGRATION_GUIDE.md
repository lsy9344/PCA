# 마이그레이션 가이드

## 📋 개요

기존 코드에서 새로운 클린 아키텍처 기반 구조로의 마이그레이션 가이드입니다.

## 🔄 주요 변경사항

### 1. 아키텍처 변경

**기존 구조:**
```
├── stores/
│   ├── base_store.py
│   ├── a_store.py
│   └── store_router.py
├── discount_rules/
│   ├── base_discount.py
│   └── a_discount.py
├── config/
│   └── global_config.py
└── utils/
    ├── telegram_notifier.py
    └── logger.py
```

**새로운 구조:**
```
├── core/domain/models/          # 도메인 모델
├── core/application/use_cases/  # 비즈니스 로직
├── infrastructure/config/       # 설정 관리 (YAML 기반)
├── infrastructure/web_automation/ # 웹 크롤링
├── infrastructure/notifications/ # 알림 시스템
└── interfaces/                  # API/CLI 인터페이스
```

### 2. 설정 관리 변경

**기존 (Python 파일):**
```python
# config/global_config.py
STORE_CONFIGS = {
    "A": {
        "WEBSITE_URL": "...",
        "LOGIN": {"USERNAME": "...", "PASSWORD": "..."},
        "DISCOUNT_TYPES": {...}
    }
}
```

**새로운 (YAML 파일):**
```yaml
# infrastructure/config/store_configs/a_store_config.yaml
store:
  id: "A"
  website_url: "..."
login:
  username: "..."
  password: "..."
coupons:
  FREE_1HOUR:
    name: "..."
    type: "free"
```

### 3. 의존성 주입 도입

**기존 (직접 의존성):**
```python
class AStore(BaseStore):
    def __init__(self):
        self.config = STORE_CONFIGS["A"]
        self.telegram = TelegramNotifier(...)
```

**새로운 (의존성 주입):**
```python
class AStoreCrawler(BaseCrawler):
    def __init__(self, store_config, playwright_config, logger):
        self.store_config = store_config
        self.logger = logger
```

## 🚀 마이그레이션 단계

### 1단계: 설정 파일 변환

기존 `config/global_config.py`의 내용을 YAML 파일로 변환:

```bash
# A매장 설정 변환
python scripts/convert_config.py --store A --output infrastructure/config/store_configs/a_store_config.yaml
```

### 2단계: 기존 A매장 코드 검증

새로운 A매장 크롤러가 기존 로직과 동일하게 작동하는지 확인:

```bash
# 기존 방식으로 테스트
python test_a_store.py

# 새로운 방식으로 테스트
python interfaces/cli/main.py --store A --vehicle 12가3456
```

### 3단계: B매장 구현

새로운 아키텍처로 B매장 크롤러 구현:

1. **설정 파일 작성**: `infrastructure/config/store_configs/b_store_config.yaml`
2. **크롤러 구현**: `infrastructure/web_automation/store_crawlers/b_store_crawler.py`
3. **팩토리 등록**: `AutomationFactory`에 B매장 추가

### 4단계: 기존 파일 정리

마이그레이션 완료 후 기존 파일들을 정리:

```bash
# 백업 디렉토리로 이동
mkdir legacy_backup
mv stores/ legacy_backup/
mv discount_rules/ legacy_backup/
mv config/global_config.py legacy_backup/
```

## 🔧 호환성 유지

### Lambda 핸들러 호환성

기존 Lambda 호출 방식과 호환성 유지:

```python
# 기존 방식
{
    "store_name": "A",
    "car_number": "12가3456"
}

# 새로운 방식 (하위 호환)
{
    "store_id": "A",        # 새로운 필드명
    "vehicle_number": "12가3456",  # 새로운 필드명
    "store_name": "A",      # 기존 호환성
    "car_number": "12가3456"  # 기존 호환성
}
```

### 로그 포맷 호환성

기존 로그 분석 도구와의 호환성을 위해 로그 포맷 유지:

```
[매장][단계] 메시지 | 구조화된_데이터
```

## 🧪 테스트 전략

### 1. 기능 동등성 테스트

```python
# tests/migration/test_functionality_parity.py
def test_a_store_login_parity():
    """기존 A매장 로그인과 새 구현의 동등성 테스트"""
    # 기존 방식 결과
    old_result = run_old_a_store_login()
    
    # 새로운 방식 결과
    new_result = run_new_a_store_login()
    
    assert old_result == new_result
```

### 2. 성능 비교 테스트

```python
def test_performance_comparison():
    """기존 구현 대비 성능 비교"""
    old_time = measure_old_implementation()
    new_time = measure_new_implementation()
    
    # 성능 저하가 20% 이내인지 확인
    assert new_time <= old_time * 1.2
```

### 3. 설정 변환 검증

```python
def test_config_conversion():
    """설정 변환이 올바른지 검증"""
    old_config = load_old_config()
    new_config = load_new_config()
    
    assert old_config["A"]["WEBSITE_URL"] == new_config.website_url
```

## 📊 마이그레이션 체크리스트

### 필수 작업

- [ ] 설정 파일 YAML 변환 완료
- [ ] A매장 크롤러 동작 검증
- [ ] B매장 크롤러 구현 및 테스트
- [ ] Lambda 핸들러 호환성 확인
- [ ] 텔레그램 알림 동작 확인
- [ ] 로그 포맷 호환성 확인

### 선택 작업

- [ ] 기존 파일 백업 및 정리
- [ ] 성능 최적화
- [ ] 추가 매장 확장 준비
- [ ] 모니터링 대시보드 업데이트

## 🚨 주의사항

### 1. 설정 보안

- 기존 하드코딩된 로그인 정보를 환경변수로 이전 권장
- YAML 파일에 민감한 정보 노출 주의

### 2. 브라우저 호환성

- Playwright 버전 업데이트로 인한 셀렉터 변경 가능성
- 각 매장 사이트의 HTML 구조 변경 모니터링 필요

### 3. 의존성 관리

- 새로운 패키지 의존성 추가로 인한 Lambda 패키지 크기 증가
- 필요시 Lambda Layer 활용 고려

## 🔄 롤백 계획

마이그레이션 실패 시 롤백 절차:

1. **즉시 롤백**: 기존 Lambda 함수로 트래픽 전환
2. **설정 복원**: 기존 `global_config.py` 복원
3. **의존성 복원**: 기존 `requirements.txt` 복원
4. **코드 복원**: `legacy_backup/` 디렉토리에서 파일 복원

## 📞 지원

마이그레이션 과정에서 문제 발생 시:

1. **로그 확인**: `result_logs/` 디렉토리의 상세 로그 분석
2. **텔레그램 알림**: 실패 알림을 통한 즉시 문제 파악
3. **테스트 실행**: 단위/통합 테스트로 문제 범위 특정 