# WebSocket 및 인증 UI 수정 사항 요약

## 📋 수정 개요

**날짜**: 2025-10-04  
**작업 범위**: WebSocket 연결 오류 및 인증 상태 UI 버그 수정

---

## 🐛 해결된 문제들

### 1. 로그아웃 상태 WebSocket 에러 ✅
**문제**: 로그인하지 않은 상태로 채팅 페이지 접근 시 WebSocket connection failed 에러 발생

**원인**: 인증 없이도 WebSocket 연결을 시도함

**해결**:
- `ChatPage.tsx`에서 `useAuth()` 훅으로 로그인 상태 확인
- 로그아웃 상태일 때는 WebSocket 연결 시도하지 않음

```typescript
// src/pages/ChatPage.tsx
if (!user) {
  setWsConnected(false);
  return; // 로그인 안 되어 있으면 연결 안 함
}
```

---

### 2. 로그인/회원가입 버튼 미작동 ✅
**문제**: 헤더의 로그인, 회원가입 버튼이 작동하지 않음

**원인**: 이전 코드에서는 하드코딩된 정적 버튼이었음

**해결**:
- React Router의 `<Link>` 컴포넌트로 변경
- 올바른 경로로 라우팅 (`/login`, `/signup`)

```typescript
// src/components/Header.tsx
<Link to="/login">
  <Button variant="ghost">로그인</Button>
</Link>
```

---

### 3. 로그인 후에도 로그인/회원가입 버튼 표시 ✅
**문제**: 로그인 성공 후에도 헤더에 "로그인/회원가입" 버튼이 그대로 떠 있음

**원인**: Header 컴포넌트가 AuthContext를 사용하지 않아서 인증 상태를 모름

**해결**:
- `useAuth()` 훅으로 현재 로그인 상태 확인
- 조건부 렌더링으로 로그인/로그아웃 UI 분기
- 로그인 시: 사용자 이름 + 드롭다운 메뉴 표시
- 로그아웃 시: 로그인/회원가입 버튼 표시

```typescript
// src/components/Header.tsx
const { user, logout, isLoading } = useAuth();

{user ? (
  // 로그인 상태: 드롭다운 메뉴
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <Button variant="ghost">{user.username}</Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent>
      <DropdownMenuItem onClick={handleLogout}>로그아웃</DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
) : (
  // 로그아웃 상태: 로그인/회원가입 버튼
  <>
    <Link to="/login">로그인</Link>
    <Link to="/signup">회원가입</Link>
  </>
)}
```

---

### 4. WebSocket 중복 연결 ✅
**문제**: 채팅 페이지에 접속하면 WebSocket이 2번 연결됨 (React Strict Mode 이중 마운트)

**원인**: 
- React 개발 모드의 Strict Mode가 컴포넌트를 2번 마운트
- 연결 상태 체크 로직 부재

**해결**:
- `wsClientRef.current?.isConnected()` 체크 추가
- 이미 연결되어 있으면 새 연결 생성하지 않음

```typescript
// src/pages/ChatPage.tsx
useEffect(() => {
  if (wsClientRef.current?.isConnected()) {
    console.log('[STOMP] Already connected, skipping duplicate connection');
    return; // 이미 연결되어 있으면 중단
  }
  
  // ... WebSocket 연결 로직
}, [user]);
```

---

## 📁 수정된 파일

### 1. `backtest_fe/src/components/Header.tsx`
**변경 사항**:
- `useAuth()` 훅 추가로 인증 상태 감지
- 조건부 렌더링으로 로그인/로그아웃 UI 분기
- 드롭다운 메뉴 추가:
  - 프로필 링크 (`/profile`)
  - 로그아웃 버튼 (toast 알림 포함)
- LogOut 아이콘 추가 (`lucide-react`)

**주요 코드**:
```typescript
import { useAuth } from '@/shared/contexts/AuthContext';
import { LogOut, User } from 'lucide-react';

const { user, logout, isLoading } = useAuth();

const handleLogout = async () => {
  await logout();
  toast.success('로그아웃 성공');
  navigate('/');
};
```

### 2. `backtest_fe/src/pages/ChatPage.tsx`
**변경 사항**:
- 로그인 상태 체크 추가 (`if (!user) return;`)
- WebSocket 중복 연결 방지 (`isConnected()` 체크)
- 더 명확한 로그 메시지

**주요 코드**:
```typescript
const { user } = useAuth();

useEffect(() => {
  if (!user) {
    setWsConnected(false);
    return; // 로그인 안 되면 연결 안 함
  }

  if (wsClientRef.current?.isConnected()) {
    return; // 이미 연결되어 있으면 중단
  }

  // WebSocket 연결 로직...
}, [user]);
```

### 3. Docker 서비스명 변경 (이전 작업)
**변경 사항**:
- 모든 Docker 컨테이너명에서 언더스코어(`_`)를 하이픈(`-`)으로 변경
- 예: `backtest_be_spring` → `backtest-be-spring`
- 이유: Tomcat 10.1이 Host 헤더의 언더스코어를 거부함

**영향받은 파일**:
- `compose/compose.dev.yaml`
- `.env.local`
- `backtest_fe/vite.config.ts`

### 4. WebSocket URL 빌더 (이전 작업)
**변경 사항**:
- 개발 모드에서 Vite 프록시 우회
- 직접 `ws://localhost:8080/ws`로 연결
- 이유: Vite 프록시가 WebSocket pathname을 '/'로 변경하는 버그

**파일**: `backtest_fe/src/shared/api/ws.ts`
```typescript
export function buildWebSocketUrl(path: string): string {
  if (window.location.host === 'localhost:5173') {
    // 개발 모드: 백엔드에 직접 연결
    return 'ws://localhost:8080/ws';
  }
  // 프로덕션: Nginx 프록시 사용
  return `${wsBaseUrl}${path}`;
}
```

---

## 🧪 테스트 방법

### 로컬 환경 실행
```bash
# 전체 스택 시작
docker compose -f compose/compose.dev.yaml up -d --build

# 서비스 상태 확인
docker compose -f compose/compose.dev.yaml ps

# 로그 확인
docker compose -f compose/compose.dev.yaml logs -f backtest-fe
docker compose -f compose/compose.dev.yaml logs -f backtest-be-spring
```

### 브라우저 테스트
1. http://localhost:5173 접속
2. **Ctrl + Shift + R**로 하드 리프레시 (캐시 무시)
3. F12로 개발자 도구 열기
4. 상세한 테스트 시나리오는 `BROWSER_TEST_CHECKLIST.md` 참조

### 통합 테스트 스크립트
```bash
# 자동화된 헬스 체크
./test_integration.sh
```

---

## 🎯 검증 포인트

### 1. 로그아웃 상태
- ✅ 채팅 페이지 접속 시 WebSocket 에러 없음
- ✅ 헤더에 "로그인/회원가입" 버튼 표시
- ✅ 버튼 클릭 시 로그인/회원가입 페이지로 이동

### 2. 로그인 상태
- ✅ 헤더에 사용자 이름 표시
- ✅ 드롭다운 메뉴 정상 작동 (프로필, 로그아웃)
- ✅ 채팅 페이지에서 WebSocket 1개만 연결
- ✅ 로그아웃 시 토스트 메시지 + 리다이렉트

### 3. WebSocket 연결
- ✅ 개발자 도구 Console에서 중복 연결 로그 없음
- ✅ Network 탭 WS 필터에서 1개의 연결만 확인
- ✅ STOMP 프로토콜 정상 작동 (CONNECT → CONNECTED)

---

## 📚 관련 문서

- `BROWSER_TEST_CHECKLIST.md` - 상세 브라우저 테스트 가이드
- `test_integration.sh` - 자동화된 통합 테스트 스크립트
- `backtest_fe/README.md` - 프론트엔드 개발 가이드
- `backtest_be_spring/README.md` - Spring Boot 백엔드 가이드

---

## 🔄 향후 개선 사항

### 프로덕션 빌드 테스트
- [ ] `docker compose -f compose/compose.prod.yaml` 환경에서 검증
- [ ] Nginx 프록시를 통한 WebSocket 연결 테스트
- [ ] SSL/TLS 적용 시 WSS 프로토콜 확인

### 에러 핸들링 강화
- [ ] WebSocket 재연결 로직 개선
- [ ] 네트워크 오류 시 사용자 친화적 메시지
- [ ] 토큰 만료 시 자동 로그아웃 및 알림

### 성능 최적화
- [ ] WebSocket 연결 풀링
- [ ] 메시지 페이징 및 무한 스크롤
- [ ] 대용량 채팅방 처리 최적화

---

## 👥 기여자

- WebSocket 연결 오류 수정
- 인증 UI 상태 관리 개선
- 중복 연결 방지 로직 구현
- Docker 네이밍 컨벤션 표준화

---

**마지막 업데이트**: 2025-10-04  
**테스트 환경**: Docker Compose (dev)  
**프론트엔드**: React 18 + Vite 4.5.14  
**백엔드**: Spring Boot 3.4.3 (WebSocket/STOMP)
