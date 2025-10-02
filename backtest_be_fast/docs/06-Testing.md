# FastAPI 백엔드 테스트 가이드

## 테스트 실행 방법

### 가상환경 설정 (최초 1회)

```bash
cd backtest_be_fast

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\activate  # Windows

# 프로덕션 의존성 설치
pip install -r requirements.txt

# 테스트 의존성 설치
pip install -r requirements-test.txt
```

### 단위 테스트 실행

```bash
# 모든 단위 테스트 실행
PYTHONPATH=. pytest tests/unit/ -v

# 특정 테스트 파일 실행
PYTHONPATH=. pytest tests/unit/test_asset_entity.py -v

# 특정 테스트 클래스 실행
PYTHONPATH=. pytest tests/unit/test_asset_entity.py::TestAssetEntity -v

# 특정 테스트 메서드 실행
PYTHONPATH=. pytest tests/unit/test_asset_entity.py::TestAssetEntity::test_자산_생성_성공 -v
```

### 커버리지와 함께 실행

```bash
# 전체 커버리지
PYTHONPATH=. pytest tests/unit/ --cov=app --cov-report=html --cov-report=term

# 특정 모듈 커버리지
PYTHONPATH=. pytest tests/unit/ --cov=app/domains/portfolio --cov-report=term-missing

# HTML 리포트 생성 후 브라우저에서 확인
PYTHONPATH=. pytest tests/unit/ --cov=app --cov-report=html
# 그 다음 htmlcov/index.html 파일을 브라우저에서 열기
```

### 테스트 마커로 필터링

```bash
# 단위 테스트만 실행
PYTHONPATH=. pytest -m unit -v

# 통합 테스트만 실행
PYTHONPATH=. pytest -m integration -v

# E2E 테스트만 실행
PYTHONPATH=. pytest -m e2e -v

# DB 테스트 제외
PYTHONPATH=. pytest -m "not db" -v

# 느린 테스트 제외
PYTHONPATH=. pytest -m "not slow" -v
```

### 병렬 실행 (빠른 실행)

```bash
# pytest-xdist 설치 필요
pip install pytest-xdist

# 자동으로 CPU 코어 수만큼 병렬 실행
PYTHONPATH=. pytest tests/unit/ -n auto

# 4개 워커로 병렬 실행
PYTHONPATH=. pytest tests/unit/ -n 4
```

### 실패한 테스트만 재실행

```bash
# 마지막 실행에서 실패한 테스트만 재실행
PYTHONPATH=. pytest --lf

# 실패한 테스트를 먼저 실행하고 나머지도 실행
PYTHONPATH=. pytest --ff
```

## 현재 테스트 현황

### 단위 테스트 (Unit Tests)

- ✅ **AssetEntity**: 31개 테스트, 99% 커버리지
- ✅ **PortfolioEntity**: 22개 테스트, 97% 커버리지
- **총 53개 테스트** 모두 통과

### 통합 테스트 (Integration Tests)

- 🚧 작업 예정

### E2E 테스트 (End-to-End Tests)

- 🚧 작업 예정

## 테스트 작성 가이드

### Given-When-Then 패턴

```python
def test_예시(self):
    """
    Given: 초기 상태 설명
    When: 실행할 동작
    Then: 예상 결과
    """
    # Given: 테스트 준비
    portfolio = PortfolioEntity(name="테스트", total_value=10000.0)
    
    # When: 동작 실행
    result = portfolio.get_asset_count()
    
    # Then: 결과 검증
    assert result == 0
```

### 테스트 이름 규칙

- **한글 사용 권장**: `test_포트폴리오_생성_성공`
- 또는 **영문 snake_case**: `test_create_portfolio_success`
- **동작과 예상 결과를 명확히**: `test_자산_추가_시_중복_심볼이면_에러`

### Fixture 활용

```python
@pytest.fixture
def sample_portfolio():
    """재사용 가능한 테스트 데이터"""
    return PortfolioEntity(name="테스트", total_value=10000.0)

def test_예시(sample_portfolio):
    # fixture를 파라미터로 받아 사용
    assert sample_portfolio.total_value == 10000.0
```

## CI/CD에서 테스트

GitHub Actions에서 자동으로 실행됩니다:

```yaml
- name: Run Unit Tests
  run: |
    cd backtest_be_fast
    PYTHONPATH=. pytest tests/unit -v --cov=app --cov-report=xml
```

## Docker에서 테스트

```bash
# Docker Compose로 테스트 환경 구성
docker compose -f compose/compose.dev.yaml up -d mysql redis

# 컨테이너 내에서 테스트 실행
docker compose -f compose/compose.dev.yaml run --rm backtest_be_fast \
    pytest tests/unit/ -v

# 커버리지 포함
docker compose -f compose/compose.dev.yaml run --rm backtest_be_fast \
    pytest tests/unit/ --cov=app --cov-report=term
```

## 문제 해결

### ImportError 발생 시

```bash
# PYTHONPATH 설정 확인
export PYTHONPATH=.
pytest tests/unit/ -v
```

### 비동기 테스트 오류 시

```bash
# pytest-asyncio 버전 확인
pip list | grep pytest-asyncio

# 최신 버전으로 업그레이드
pip install --upgrade pytest-asyncio
```

### DB 연결 오류 시

```bash
# 테스트용 MySQL 시작
docker compose -f compose/compose.dev.yaml up -d mysql

# 연결 확인
mysql -h localhost -u test -ptest -e "SELECT 1"
```

## 추가 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-asyncio 문서](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py 문서](https://coverage.readthedocs.io/)
- [테스트 전략 가이드](./docs/05-Test-Strategy.md)
