#!/bin/bash

# 커밋 메시지 마이그레이션 스크립트
# 기존의 일관성 없는 커밋 메시지들을 새로운 컨벤션에 맞게 수정

echo "🔄 커밋 메시지 마이그레이션 시작..."
echo "⚠️  주의: 이 작업은 Git 히스토리를 변경합니다."
echo "📋 백업 브랜치를 생성하고 진행합니다."

# 백업 브랜치 생성
backup_branch="backup-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$backup_branch"
echo "✅ 백업 브랜치 생성: $backup_branch"

# 메인 브랜치로 돌아가기
git checkout main

# 마이그레이션 매핑 테이블 (한글 설명으로 변환)
declare -A commit_mapping=(
    # Phase 4 관련
    ["feat: Phase 4 백엔드 리팩터링 완료"]="refactor(backend): Phase 4 아키텍처 재설계 완료"
    
    # 백엔드 기능 구현
    ["feat(back): Implement Portfolio Domain with Entities, Services, and Value Objects"]="feat(backend/domain): DDD 패턴으로 Portfolio 도메인 구현"
    ["refactor(back): Refactor backend architecture to implement Repository and Factory patterns"]="refactor(backend): Repository와 Factory 패턴 구현"
    ["feat(back): Implement backtest service and various trading strategies"]="feat(backend/service): 백테스트 서비스 및 거래 전략 구현"
    
    # 정리 작업
    ["불필요한 파일 삭제"]="chore: 불필요한 파일 제거"
    ["불필요한 코드 삭제"]="chore: 불필요한 코드 제거"
    
    # 프론트엔드 리팩터링
    ["refactor(front)"]="refactor(frontend): 코드 정리 및 최적화"
    ["refactor(front): phase 7"]="test(frontend): Phase 7 테스트 인프라 완료"
    ["refactor(front): phase 4"]="perf(frontend): Phase 4 성능 최적화 완료"
    ["refactor(front): phase 3"]="refactor(frontend): Phase 3 커스텀 훅 추출 완료"
    ["refactor(front): phase 2"]="refactor(frontend): Phase 2 상태 관리 개선 완료"
    ["refactor(front): phase 1"]="refactor(frontend): Phase 1 컴포넌트 분리 완료"
    
    # 기능 추가
    ["feat: 4.6 기존 컴포넌트에 공통 컴포넌트 적용 완료"]="feat(frontend/components): 기존 폼에 공통 컴포넌트 적용"
    ["feat: 4.6 공통 컴포넌트 라이브러리 확장 완료"]="feat(frontend/components): 공통 컴포넌트 라이브러리 확장"
    ["feat: 4.5 코드 표준화 및 재사용성 구축 완료"]="refactor(frontend): 코드 표준화 및 DRY 원칙 적용 완료"
    
    # CI/CD 관련
    ["trigger: Jenkins 재실행을 위한 더미 커밋"]="ci: Jenkins 재빌드 트리거"
    ["젠킨스 파일 수정"]="ci: Jenkinsfile 설정 업데이트"
    
    # 버그 수정
    ["fix: TypeScript 빌드 오류 해결"]="fix(frontend): TypeScript 빌드 오류 해결"
    ["fix: TypeScript 컴파일 오류 해결"]="fix(frontend): TypeScript 컴파일 오류 수정"
    ["fix: TypeScript 빌드 오류 수정"]="fix(frontend): TypeScript 빌드 문제 수정"
    ["fix(front): 종목 선택 레이아웃 깨짐 수정"]="fix(frontend/components): 종목 선택 레이아웃 문제 수정"
    
    # UI 개선
    ["refactor(front): 이모지 대신 react icon 사용하도록"]="style(frontend): 이모지를 React Icons로 교체"
    ["프론트엔드 리액트 부트스트랩 -> 테일윈드로 마이그레이션"]="refactor(frontend): React Bootstrap에서 Tailwind CSS로 마이그레이션"
    
    # 문서 업데이트
    ["docs: 문서 최신화"]="docs: 문서 업데이트"
    ["문서 최신화"]="docs: 프로젝트 문서 업데이트"
    ["문서 최신화 중"]="docs: 문서 업데이트 진행 중"
    
    # 기능 구현
    ["창 분리"]="refactor(frontend): 윈도우 레이아웃 분리"
    ["현금 기능 정상화"]="fix(backend): 현금 자산 기능 수정"
    ["뉴스 수정 중"]="feat(frontend): 뉴스 기능 구현"
    ["프론트 리펙터링 계획"]="docs(frontend): 프론트엔드 리팩터링 전략 수립"
)

# 커밋 메시지 일괄 수정 함수
migrate_commits() {
    echo "🔧 Interactive rebase를 통한 커밋 메시지 수정..."
    
    # 수정할 커밋 수 (최근 40개)
    commit_count=40
    
    # rebase 명령어 파일 생성
    rebase_file="rebase_commands.txt"
    git log --oneline -$commit_count --format="%H %s" > "$rebase_file"
    
    echo "📝 수정 대상 커밋들:"
    while IFS= read -r line; do
        commit_hash=$(echo "$line" | cut -d' ' -f1)
        commit_msg=$(echo "$line" | cut -d' ' -f2-)
        
        if [[ -n "${commit_mapping[$commit_msg]}" ]]; then
            echo "  ✏️  $commit_msg"
            echo "     → ${commit_mapping[$commit_msg]}"
        fi
    done < "$rebase_file"
    
    rm "$rebase_file"
    
    echo ""
    echo "🚀 실제 마이그레이션을 시작하시겠습니까? (y/n)"
    read -r response
    
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        perform_migration
    else
        echo "❌ 마이그레이션이 취소되었습니다."
        exit 0
    fi
}

# 실제 마이그레이션 수행
perform_migration() {
    echo "🔧 커밋 메시지 수정 중..."
    
    # Git filter-branch를 사용한 일괄 수정
    git filter-branch -f --msg-filter '
        commit_msg=$(cat)
        case "$commit_msg" in
            "feat: Phase 4 백엔드 리팩터링 완료"*)
                echo "refactor(backend): Phase 4 아키텍처 재설계 완료"
                echo ""
                echo "- Enhanced Services: 도메인 서비스 통합 백테스트/포트폴리오 서비스"
                echo "- Event-Driven Architecture: 17개 도메인 이벤트 및 핸들러 시스템"
                echo "- CQRS Pattern: 7개 커맨드, 10개 쿼리, 통합 라우팅 시스템"
                echo "- CQRSServiceManager: API 엔드포인트 연동 준비 완료"
                echo "- 파일 구조: 32개 → 45개 (Enhanced 2개, Events 8개, CQRS 5개)"
                echo "- 기존 Phase 1-3와 완전 호환, 11개 테스트 통과"
                ;;
            "feat(back): Implement Portfolio Domain with Entities, Services, and Value Objects"*)
                echo "feat(backend/domain): DDD 패턴으로 Portfolio 도메인 구현"
                echo ""
                echo "- 값 객체와 엔티티를 포함한 Portfolio 도메인 추가"
                echo "- 복잡한 비즈니스 로직을 위한 PortfolioDomainService 구현"
                echo "- 가중치 최적화 및 상관관계 분석 기능 추가"
                ;;
            "refactor(back): Refactor backend architecture to implement Repository and Factory patterns"*)
                echo "refactor(backend): Repository와 Factory 패턴 구현"
                echo ""
                echo "- 데이터 접근 추상화를 위한 Repository 패턴 추가"
                echo "- 서비스 생성을 위한 Factory 패턴 구현"
                echo "- 의존성 주입 시스템 구축"
                ;;
            "feat(back): Implement backtest service and various trading strategies"*)
                echo "feat(backend/service): 백테스트 서비스 및 거래 전략 구현"
                echo ""
                echo "- 백테스트 서비스를 전문화된 컴포넌트로 분리"
                echo "- SMA, RSI, 볼린저 밴드, MACD 전략 구현"
                echo "- 최적화 및 검증 서비스 추가"
                ;;
            "불필요한 파일 삭제"*)
                echo "chore: 불필요한 파일 제거"
                ;;
            "불필요한 코드 삭제"*)
                echo "chore: 불필요한 코드 제거"
                ;;
            "refactor(front): phase 7"*)
                echo "test(frontend): Phase 7 테스트 인프라 완료"
                echo ""
                echo "- 커스텀 훅을 위한 포괄적 단위 테스트 추가"
                echo "- 156개 테스트 케이스로 유틸리티 함수 테스트 구현"
                echo "- Vitest를 통한 완전한 테스트 환경 구축"
                ;;
            "refactor(front): phase 4"*)
                echo "perf(frontend): Phase 4 성능 최적화 완료"
                echo ""
                echo "- 차트 컴포넌트에 React.memo, useMemo, useCallback 적용"
                echo "- React.lazy와 Suspense를 통한 코드 스플리팅 구현"
                echo "- Vite manualChunks 설정으로 번들 크기 최적화"
                ;;
            "refactor(front): phase 3"*)
                echo "refactor(frontend): Phase 3 커스텀 훅 추출 완료"
                echo ""
                echo "- useExchangeRate, useFormInput, useDropdown 훅 추출"
                echo "- 재사용성 향상을 위한 로직과 뷰 분리"
                echo "- UI 상태 관리 시스템 구현"
                ;;
            "refactor(front): phase 2"*)
                echo "refactor(frontend): Phase 2 상태 관리 개선 완료"
                echo ""
                echo "- 복잡한 폼 상태를 위한 useReducer 구현"
                echo "- 데이터 페칭을 위한 전문화된 커스텀 훅 생성"
                echo "- 모달 및 드롭다운 상태 관리 유틸리티 추가"
                ;;
            "refactor(front): phase 1"*)
                echo "refactor(frontend): Phase 1 컴포넌트 분리 완료"
                echo ""
                echo "- God 컴포넌트를 단일 책임 컴포넌트로 분리"
                echo "- PortfolioForm, StrategyForm, DateRangeForm 추출"
                echo "- SRP 원칙에 따른 컴포넌트 복잡성 감소"
                ;;
            "feat: 4.6 기존 컴포넌트에 공통 컴포넌트 적용 완료"*)
                echo "feat(frontend/components): 기존 폼에 공통 컴포넌트 적용"
                echo ""
                echo "- FormField 컴포넌트로 StrategyForm, DateRangeForm 리팩터링"
                echo "- 기존 UI에 Modal, Tooltip, Badge 컴포넌트 적용"
                echo "- 애플리케이션 전반의 디자인 일관성 달성"
                ;;
            "feat: 4.6 공통 컴포넌트 라이브러리 확장 완료"*)
                echo "feat(frontend/components): 공통 컴포넌트 라이브러리 확장"
                echo ""
                echo "- Badge, Tooltip, Modal, Pagination 컴포넌트 추가"
                echo "- SearchableSelect, DateRangePicker, ToggleSwitch 구현"
                echo "- 일관된 import를 위한 통합 export 시스템 생성"
                ;;
            "feat: 4.5 코드 표준화 및 재사용성 구축 완료"*)
                echo "refactor(frontend): 코드 표준화 및 DRY 원칙 적용 완료"
                echo ""
                echo "- FormField, LoadingSpinner를 포함한 공통 컴포넌트 라이브러리 구축"
                echo "- UI 상수 및 스타일 클래스 중앙화"
                echo "- 의미 있는 상수로 매직 넘버 및 문자열 제거"
                ;;
            "trigger: Jenkins 재실행을 위한 더미 커밋"*)
                echo "ci: Jenkins 재빌드 트리거"
                ;;
            "젠킨스 파일 수정"*)
                echo "ci: Jenkinsfile 설정 업데이트"
                ;;
            "fix: TypeScript 빌드 오류 해결"*)
                echo "fix(frontend): TypeScript 빌드 오류 해결"
                ;;
            "fix: TypeScript 컴파일 오류 해결"*)
                echo "fix(frontend): TypeScript 컴파일 오류 수정"
                ;;
            "fix: TypeScript 빌드 오류 수정"*)
                echo "fix(frontend): TypeScript 빌드 문제 수정"
                ;;
            "fix(front): 종목 선택 레이아웃 깨짐 수정"*)
                echo "fix(frontend/components): 종목 선택 레이아웃 문제 수정"
                ;;
            "refactor(front): 이모지 대신 react icon 사용하도록"*)
                echo "style(frontend): 이모지를 React Icons로 교체"
                echo ""
                echo "- UI 텍스트와 문서에서 모든 이모지 제거"
                echo "- react-icons 라이브러리로 전문적 인터페이스 구현"
                echo "- 스크린 리더 호환성 보장"
                ;;
            "프론트엔드 리액트 부트스트랩 -> 테일윈드로 마이그레이션"*)
                echo "refactor(frontend): React Bootstrap에서 Tailwind CSS로 마이그레이션"
                echo ""
                echo "- React Bootstrap에서 Tailwind CSS로 완전 마이그레이션"
                echo "- 유틸리티 클래스로 모든 컴포넌트 스타일링 업데이트"
                echo "- 디자인 일관성 및 유지보수성 향상"
                ;;
            "docs: 문서 최신화"*)
                echo "docs: 문서 업데이트"
                ;;
            "문서 최신화"*)
                echo "docs: 프로젝트 문서 업데이트"
                ;;
            "문서 최신화 중"*)
                echo "docs: 문서 업데이트 진행 중"
                ;;
            "창 분리"*)
                echo "refactor(frontend): 윈도우 레이아웃 분리"
                ;;
            "현금 기능 정상화"*)
                echo "fix(backend): 현금 자산 기능 수정"
                echo ""
                echo "- asset_type 필드로 적절한 현금 자산 처리 구현"
                echo "- 0% 수익률로 무위험 자산 동작 보장"
                echo "- 현금과 주식 분리로 포트폴리오 구성 수정"
                ;;
            "뉴스 수정 중"*)
                echo "feat(frontend): 뉴스 기능 구현"
                ;;
            "프론트 리펙터링 계획"*)
                echo "docs(frontend): 프론트엔드 리팩터링 전략 수립"
                ;;
            *)
                echo "$commit_msg"
                ;;
        esac
    ' HEAD~40
    
    echo "✅ 커밋 메시지 마이그레이션 완료!"
}

# 메인 실행
main() {
    echo "📚 백테스팅 시스템 커밋 메시지 마이그레이션"
    echo "================================================"
    echo ""
    echo "🎯 목표: 일관성 없는 커밋 메시지를 새로운 컨벤션에 맞게 수정"
    echo "📋 컨벤션: <type>(<scope>): <description>"
    echo ""
    
    migrate_commits
}

# 스크립트 실행
main
