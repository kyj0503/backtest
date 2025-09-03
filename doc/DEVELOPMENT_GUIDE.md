# 개발 가이드

백테스팅 시스템 개발을 위한 종합 가이드입니다.

## 개발 규칙

### 커밋 메시지 규칙
```
형식: type: 간결한 제목
- 이모지 사용 금지
- 불필요한 수식어 제거
- 명확하고 구체적인 내용

예시:
✅ fix: TypeScript 빌드 오류 해결
✅ feat: 현금 자산 처리 기능 추가
✅ docs: API 문서 업데이트
❌ fix: 버그 수정 완료!!!
❌ feat: 멋진 새 기능 추가
```

### 코드 품질 관리
- **TypeScript**: strict 모드 적용, any 타입 금지
- **Python**: type hints 필수, Pydantic V2 검증
- **테스트**: 단위/통합/E2E 테스트 커버리지 80% 이상
- **린팅**: ESLint + Prettier (프론트엔드), black + isort (백엔드)

### 파일 구조 규칙
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API 엔드포인트 (기능별 분리)
│   ├── models/               # Pydantic 모델 (requests/responses)
│   ├── services/             # 비즈니스 로직 (서비스별 분리)
│   └── utils/                # 공통 유틸리티

frontend/
├── src/
│   ├── components/           # React 컴포넌트 (기능별)
│   ├── services/             # API 호출 서비스
│   ├── types/                # TypeScript 타입 정의
│   └── utils/                # 공통 유틸리티
```

## 투자 전략 개발

### 새 전략 추가 방법
1. **전략 클래스 생성**
```python
# strategies/my_strategy.py
from backtesting import Strategy

class MyStrategy(Strategy):
    param1 = 10
    param2 = 30
    
    def init(self):
        # 지표 초기화
        pass
    
    def next(self):
        # 매매 로직
        if self.should_buy():
            self.buy()
        elif self.should_sell():
            self.sell()
```

2. **전략 등록**
```python
# backend/app/services/strategy_service.py
from strategies.my_strategy import MyStrategy

_strategies = {
    'sma_cross': SMAStrategy,
    'rsi': RSIStrategy,
    'my_strategy': MyStrategy,  # 새 전략 추가
}
```

3. **프론트엔드 옵션 추가**
```typescript
// frontend/src/constants/strategies.ts
export const STRATEGY_OPTIONS = [
  { value: 'sma_cross', label: 'SMA 크로스오버' },
  { value: 'rsi', label: 'RSI 전략' },
  { value: 'my_strategy', label: '나만의 전략' },  // 새 전략 추가
];
```

### 전략 매개변수 설정
```python
class MyStrategy(Strategy):
    # 매개변수 정의 (튜닝 가능)
    short_window = 10
    long_window = 30
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
```

## 성능 최적화

### 프론트엔드 최적화
- **코드 분할**: React.lazy로 컴포넌트 지연 로딩
- **메모이제이션**: React.memo, useMemo, useCallback 활용
- **번들 최적화**: Vite 빌드 최적화 설정

### 백엔드 최적화
- **비동기 처리**: asyncio를 활용한 동시 데이터 수집
- **캐싱 전략**: Redis 메모리 캐시 추가 계획
- **데이터베이스**: 인덱스 최적화 및 쿼리 튜닝

### 인프라 최적화
- **Docker 이미지**: 멀티 스테이지 빌드로 이미지 크기 최소화
- **nginx**: 정적 파일 캐싱 및 gzip 압축
- **로드 밸런싱**: 향후 다중 인스턴스 배포 계획

## 보안 고려사항

### 입력 검증
- **Pydantic V2**: 모든 API 입력 데이터 검증
- **SQL 인젝션**: 파라미터화된 쿼리 사용
- **XSS 방지**: 사용자 입력 이스케이프 처리

### 인증 및 권한
- **JWT 토큰**: 사용자 인증 (향후 구현)
- **CORS**: 허용된 도메인만 API 접근
- **레이트 리미팅**: API 호출 횟수 제한

### 환경 변수 관리
```bash
# .env 파일 예시
MYSQL_HOST=host.docker.internal
MYSQL_PASSWORD=secure_password
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

## 모니터링

### 애플리케이션 모니터링
- **로그 수집**: 구조화된 JSON 로그
- **에러 추적**: 실시간 에러 알림
- **성능 메트릭**: API 응답 시간, 메모리 사용량

### 인프라 모니터링
- **컨테이너 상태**: Docker 컨테이너 헬스 체크
- **데이터베이스**: MySQL 연결 상태 및 성능
- **네트워크**: API 엔드포인트 가용성

## 문제 해결 가이드

### 일반적인 문제들

1. **TypeScript 빌드 오류**
   - 원인: 타입 정의 불일치
   - 해결: `npm run type-check`로 타입 오류 확인

2. **백테스트 실행 실패**
   - 원인: 데이터 수집 실패 또는 전략 오류
   - 해결: 로그 확인 후 데이터 소스 및 전략 검증

3. **Docker 컨테이너 시작 실패**
   - 원인: 포트 충돌 또는 의존성 문제
   - 해결: `docker-compose logs` 확인 후 포트 변경

### 디버깅 도구
- **프론트엔드**: React DevTools, Browser DevTools
- **백엔드**: FastAPI 자동 문서, Python 디버거
- **인프라**: Docker logs, Jenkins 빌드 로그

## 기여 가이드

### 개발 프로세스
1. **이슈 생성**: GitHub Issues에 기능 요청 또는 버그 리포트
2. **브랜치 생성**: `feature/기능명` 또는 `fix/버그명`
3. **개발 및 테스트**: 로컬에서 개발 후 테스트 실행
4. **Pull Request**: 코드 리뷰 요청
5. **머지**: 리뷰 승인 후 main 브랜치로 머지

### 코드 리뷰 체크리스트
- [ ] 코드 품질: 가독성, 성능, 보안
- [ ] 테스트: 단위 테스트 작성 및 통과
- [ ] 문서: README 및 API 문서 업데이트
- [ ] 호환성: 기존 기능과의 호환성 확인
