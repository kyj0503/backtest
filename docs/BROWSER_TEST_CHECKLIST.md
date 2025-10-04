# 브라우저 테스트 체크리스트

## 테스트 준비
1. 브라우저에서 http://localhost:5173 접속
2. **Ctrl + Shift + R** 또는 **Cmd + Shift + R** (하드 리프레시 - 캐시 무시)
3. 브라우저 개발자 도구 열기 (F12)
   - Console 탭 열기 (WebSocket 로그 확인용)
   - Network 탭 열기 (WS 필터 적용)

---

## ✅ 테스트 시나리오

### 1. 로그아웃 상태에서 채팅 페이지 접근
**예상 동작:**
- ❌ ~~WebSocket connection error 발생~~ (이전 문제)
- ✅ WebSocket 연결 시도 안함 (콘솔에 에러 없음)
- ✅ 채팅 기능이 비활성화되어 있거나 로그인 유도 메시지 표시

**검증 방법:**
```
1. 헤더에서 "채팅" 탭 클릭
2. 콘솔에서 WebSocket 관련 에러가 없는지 확인
3. Network 탭 → WS 필터 → WebSocket 연결 없어야 함
```

**콘솔 예상 출력:**
```
(WebSocket 연결 로그 없음)
```

---

### 2. 로그인/회원가입 버튼 동작
**예상 동작:**
- ✅ "로그인" 버튼 클릭 시 로그인 페이지로 이동
- ✅ "회원가입" 버튼 클릭 시 회원가입 페이지로 이동
- ✅ 양식 제출 시 정상 동작

**검증 방법:**
```
1. 헤더 우측 상단의 "로그인" 버튼 클릭
2. 로그인 페이지(/login)로 이동 확인
3. 테스트 계정으로 로그인 시도
4. Network 탭에서 POST /api/auth/login 요청 성공 확인 (HTTP 200)
```

---

### 3. 로그인 후 헤더 UI 상태
**이전 문제:**
- ❌ 로그인 후에도 "로그인/회원가입" 버튼이 그대로 표시됨

**예상 동작:**
- ✅ "로그인/회원가입" 버튼 사라짐
- ✅ 우측 상단에 **사용자 이름** 표시
- ✅ 사용자 이름 옆에 아래 화살표 아이콘 표시 (드롭다운)

**검증 방법:**
```
1. 로그인 완료 후 메인 페이지로 리다이렉트
2. 헤더 우측 상단 확인:
   - 사용자 이름이 표시되어야 함 (예: "홍길동")
   - 아래 화살표(▼) 아이콘이 있어야 함
3. localStorage에 'token' 키가 존재하는지 확인:
   - 개발자도구 → Application 탭 → Local Storage → http://localhost:5173
   - 'token' 키에 JWT 토큰 값이 있어야 함
```

**콘솔에서 확인:**
```javascript
// 개발자도구 Console에서 실행
localStorage.getItem('token')
// 예상 출력: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." (JWT 토큰)
```

---

### 4. 사용자 드롭다운 메뉴
**예상 동작:**
- ✅ 사용자 이름 클릭 시 드롭다운 메뉴 표시
- ✅ "프로필" 링크 클릭 시 프로필 페이지(/profile)로 이동
- ✅ "로그아웃" 버튼 클릭 시:
  - localStorage에서 token 제거
  - "로그아웃 성공" 토스트 메시지 표시
  - 메인 페이지(/)로 리다이렉트
  - 헤더가 다시 "로그인/회원가입" 버튼으로 변경

**검증 방법:**
```
1. 로그인된 상태에서 헤더의 사용자 이름 클릭
2. 드롭다운 메뉴가 열리는지 확인:
   - "프로필" 항목 (사용자 아이콘과 함께)
   - "로그아웃" 항목 (LogOut 아이콘과 함께)
3. "프로필" 클릭 → /profile 페이지로 이동 확인
4. 다시 헤더 드롭다운 열고 "로그아웃" 클릭
5. 토스트 메시지 "로그아웃 성공" 확인
6. 메인 페이지로 리다이렉트 확인
7. 헤더에 다시 "로그인/회원가입" 버튼 표시 확인
```

**콘솔에서 확인:**
```javascript
// 로그아웃 후 실행
localStorage.getItem('token')
// 예상 출력: null
```

---

### 5. 로그인 상태에서 채팅 페이지 - WebSocket 연결
**이전 문제:**
- ❌ WebSocket 연결이 2번 발생 (React Strict Mode 문제)
- ❌ 중복 연결로 인한 메시지 중복 수신 가능성

**예상 동작:**
- ✅ WebSocket 연결이 **딱 1번만** 발생
- ✅ STOMP 프로토콜로 정상 연결
- ✅ 채팅방 구독 성공
- ✅ 메시지 송수신 정상 작동

**검증 방법:**
```
1. 로그인 상태에서 "채팅" 탭 클릭
2. Network 탭 → WS 필터 적용
3. WebSocket 연결이 1개만 있는지 확인:
   - 이름: ws (ws://localhost:8080/ws)
   - Status: 101 Switching Protocols
4. Console 탭에서 WebSocket 로그 확인
5. 채팅 메시지 전송 테스트
6. 다른 사용자로 로그인한 창에서 메시지 수신 확인
```

**콘솔 예상 출력:**
```
[WebSocket] Dev mode - connecting directly to backend: ws://localhost:8080/ws
[STOMP] Connecting to: ws://localhost:8080/ws
[STOMP] WebSocket connection opened
[STOMP] Sending CONNECT frame
[STOMP] Received frame: CONNECTED
[STOMP] Connection established
[STOMP] Subscribed to: /topic/chatroom/{roomId}
```

**❗ 중요: 다음 로그가 나오지 않아야 함**
```
❌ [WebSocket] Dev mode - connecting directly to backend: ws://localhost:8080/ws (2번째)
❌ [STOMP] Connecting to: ws://localhost:8080/ws (2번째)
```

---

### 6. WebSocket 연결 안정성
**예상 동작:**
- ✅ 채팅 페이지를 벗어났다가 다시 돌아와도 정상 연결
- ✅ 브라우저 탭 전환 후에도 연결 유지
- ✅ 페이지 새로고침(F5) 후 재연결 성공

**검증 방법:**
```
1. 채팅 페이지에서 다른 탭(예: 백테스트)으로 이동
2. Console에서 "WebSocket closed" 로그 확인
3. 다시 채팅 탭으로 돌아오기
4. Console에서 새로운 WebSocket 연결 로그 확인 (1번만!)
5. F5로 페이지 새로고침
6. 재연결 후 1개의 WebSocket만 유지되는지 확인
```

---

## 🐛 알려진 제한사항

### React Strict Mode
- **개발 모드**에서는 React.StrictMode가 활성화되어 있어 컴포넌트가 2번 마운트됩니다.
- 하지만 `wsClientRef.current?.isConnected()` 체크로 중복 연결을 방지합니다.
- **프로덕션 빌드**에서는 Strict Mode가 비활성화되어 이 문제가 없습니다.

### Vite Proxy 제한
- WebSocket 연결은 Vite 프록시를 **우회**하고 직접 백엔드(localhost:8080)에 연결됩니다.
- 이유: Vite 프록시가 WebSocket upgrade 요청의 pathname을 '/'로 변경하는 버그 때문
- 프로덕션 환경에서는 Nginx가 모든 요청을 올바르게 프록시합니다.

---

## 📊 성공 기준

다음 모든 항목이 체크되면 **모든 문제 해결 완료**:

- [ ] 1. 로그아웃 상태 채팅 페이지: WebSocket 에러 없음
- [ ] 2. 로그인/회원가입 버튼: 정상 동작
- [ ] 3. 로그인 후 헤더: 사용자 이름 + 드롭다운 표시
- [ ] 4. 드롭다운 메뉴: 프로필 이동, 로그아웃 동작 정상
- [ ] 5. 로그인 상태 채팅: WebSocket 1개만 연결
- [ ] 6. WebSocket 안정성: 페이지 전환, 새로고침 정상

---

## 🔧 문제 발생 시 디버깅

### WebSocket 연결 실패 시
```bash
# Spring Boot 로그 확인
docker compose -f compose.dev.yaml logs backtest-be-spring --tail=50

# 포트 리스닝 확인
netstat -tuln | grep 8080
```

### 인증 문제 시
```bash
# FastAPI 로그 확인 (인증 서비스)
docker compose -f compose.dev.yaml logs backtest-be-fast --tail=50

# Redis 연결 확인 (세션 저장소)
docker compose -f compose.dev.yaml exec redis redis-cli ping
```

### 프론트엔드 에러 시
```bash
# Frontend 로그 확인
docker compose -f compose.dev.yaml logs backtest-fe --tail=50

# 컨테이너 재시작
docker compose -f compose.dev.yaml restart backtest-fe
```

---

## 📝 테스트 완료 후

테스트가 성공적으로 완료되면 다음 사항을 보고해주세요:

1. **성공한 항목**: 위의 6가지 시나리오 중 성공한 것들
2. **실패한 항목**: 문제가 발생한 시나리오와 에러 메시지
3. **Console 로그**: 특이사항이나 에러 로그
4. **Network 탭 스크린샷**: WebSocket 연결 상태 (선택사항)

---

**작성일**: 2025-10-04  
**테스트 환경**: Docker Compose 개발 환경 (compose.dev.yaml)  
**관련 이슈**: WebSocket 연결 실패, 인증 상태 UI 버그, 중복 연결 문제
