# 커밋 히스토리 마이그레이션 가이드

158개의 커밋을 새로운 컨벤션에 맞게 안전하게 마이그레이션하는 완전한 가이드입니다.

## 🚨 주의사항

**이 작업은 Git 히스토리를 영구적으로 변경합니다!**
- 팀원들과 사전 협의 필수
- 백업 생성 후 진행
- 테스트 환경에서 먼저 검증

## 📋 마이그레이션 단계

### 1단계: 백업 생성

```bash
# 안전한 저장소 백업
./scripts/backup_repository.sh
```

### 2단계: 현재 상태 확인

```bash
# 총 커밋 수 확인
git rev-list --count HEAD

# 컨벤션을 따르지 않는 커밋들 확인
git log --oneline | grep -v -E "^[a-f0-9]+ (feat|fix|docs|style|refactor|test|chore)(\(.+\))?: "
```

### 3단계: 테스트 마이그레이션 (권장)

```bash
# 테스트용 복제본 생성
git clone . ../backtest-migration-test
cd ../backtest-migration-test

# 테스트 마이그레이션 실행
./scripts/migrate_all_commits.sh

# 결과 검증
git log --oneline | head -20
```

### 4단계: 실제 마이그레이션

```bash
# 원본 저장소에서 실행
cd /home/ubuntu/backtest

# 마이그레이션 실행
./scripts/migrate_all_commits.sh
```

### 5단계: 검증 및 테스트

```bash
# 컨벤션 준수 확인
git log --oneline | head -20

# 백엔드 테스트 실행
docker-compose exec backend pytest tests/ -v

# 프론트엔드 테스트 실행
docker-compose exec frontend npm test
```

### 6단계: 원격 저장소 동기화

```bash
# 팀원들과 협의 후 강제 푸시
git push --force-with-lease origin main

# 다른 브랜치가 있다면 동일하게 처리
git push --force-with-lease origin develop
```

## 🔄 롤백 방법

문제가 발생한 경우:

```bash
# 1. 백업에서 복원
rm -rf /home/ubuntu/backtest
cp -r /home/ubuntu/backtest_backup_* /home/ubuntu/backtest
cd /home/ubuntu/backtest

# 2. 원격 저장소 재설정
git remote add origin <원래_원격_저장소_URL>
```

## 📝 마이그레이션 매핑 규칙

### 기존 → 새 컨벤션

| 기존 패턴 | 새 컨벤션 |
|-----------|-----------|
| `불필요한 파일 삭제` | `chore(cleanup): 불필요한 파일 삭제` |
| `문서 최신화` | `docs(readme): 문서 최신화` |
| `젠킨스 파일 수정` | `fix(ci): 젠킨스 파일 수정` |
| `프론트 리펙터링 계획` | `docs(front): 프론트엔드 리팩터링 계획 수립` |
| `feat: 설명` | `feat(core): 설명` |
| `fix: 설명` | `fix(core): 설명` |

### 자동 추론 규칙

- **"추가", "구현", "생성", "완료"** → `feat(core)`
- **"수정", "해결", "오류", "버그"** → `fix(core)`
- **"리팩터링", "개선", "최적화"** → `refactor(core)`
- **"테스트"** → `test(unit)`
- **"문서", "가이드", "README"** → `docs(readme)`
- **백엔드 관련** → `(back)` 스코프
- **프론트엔드 관련** → `(front)` 스코프

## ⚠️ 주의사항

### 마이그레이션 전
- [ ] 팀원들과 일정 협의
- [ ] 백업 생성 확인
- [ ] 테스트 환경에서 검증

### 마이그레이션 중
- [ ] 작업 브랜치에서 진행
- [ ] 단계별 확인
- [ ] 문제 발생 시 즉시 중단

### 마이그레이션 후
- [ ] 모든 테스트 통과 확인
- [ ] 컨벤션 준수 검증
- [ ] 팀원들에게 변경사항 공지

## 🔧 고급 옵션

### 선택적 마이그레이션

특정 범위의 커밋만 마이그레이션:

```bash
# 최근 20개 커밋만 마이그레이션
git filter-branch --msg-filter 'migrate_commit_message "$1"' HEAD~20..HEAD
```

### 수동 수정

자동 마이그레이션이 부정확한 경우:

```bash
# 대화형 리베이스로 수동 수정
git rebase -i HEAD~10
# 편집기에서 'reword' 선택 후 커밋 메시지 수정
```

## 📞 지원

마이그레이션 중 문제가 발생하면:
1. 작업 중단
2. 백업에서 복원
3. 팀 리드와 상의
4. 문제 해결 후 재시도
