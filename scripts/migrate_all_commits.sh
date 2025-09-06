#!/bin/bash

# 백테스팅 프로젝트 커밋 메시지 마이그레이션 스크립트
# 158개 커밋을 새로운 컨벤션(<type>(<scope>): <한글 설명>)에 맞게 변경

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# 마이그레이션 매핑 함수
migrate_commit_message() {
    local original="$1"
    local migrated=""
    
    # 기존 컨벤션 패턴들을 새 컨벤션으로 변환
    case "$original" in
        # 이미 올바른 형식
        *"feat("*"): "*)
            migrated="$original"
            ;;
        *"fix("*"): "*)
            migrated="$original"
            ;;
        *"docs("*"): "*)
            migrated="$original"
            ;;
        *"refactor("*"): "*)
            migrated="$original"
            ;;
        *"test("*"): "*)
            migrated="$original"
            ;;
        *"chore("*"): "*)
            migrated="$original"
            ;;
        
        # 스코프가 없는 기존 컨벤션
        "feat: "*)
            description="${original#feat: }"
            migrated="feat(core): $description"
            ;;
        "fix: "*)
            description="${original#fix: }"
            migrated="fix(core): $description"
            ;;
        "docs: "*)
            description="${original#docs: }"
            migrated="docs(readme): $description"
            ;;
        "refactor: "*)
            description="${original#refactor: }"
            migrated="refactor(core): $description"
            ;;
        "test: "*)
            description="${original#test: }"
            migrated="test(unit): $description"
            ;;
        "chore: "*)
            description="${original#chore: }"
            migrated="chore(deps): $description"
            ;;
        
        # 특정 패턴들
        "불필요한 파일 삭제")
            migrated="chore(cleanup): 불필요한 파일 삭제"
            ;;
        "불필요한 코드 삭제")
            migrated="refactor(cleanup): 불필요한 코드 삭제"
            ;;
        "문서 최신화"*)
            migrated="docs(readme): 문서 최신화"
            ;;
        "젠킨스 파일 수정")
            migrated="fix(ci): 젠킨스 파일 수정"
            ;;
        "trigger: Jenkins 재실행을 위한 더미 커밋")
            migrated="chore(ci): Jenkins 재실행을 위한 더미 커밋"
            ;;
        "프론트 리펙터링 계획")
            migrated="docs(front): 프론트엔드 리팩터링 계획 수립"
            ;;
        "프론트엔드 리액트 부트스트랩 -> 테일윈드로 마이그레이션")
            migrated="feat(front): 리액트 부트스트랩에서 테일윈드로 마이그레이션"
            ;;
        
        # 백엔드 관련
        *"백엔드"*|*"backend"*|*"back"*)
            if [[ "$original" =~ "리팩터링" ]]; then
                migrated="refactor(back): ${original}"
            elif [[ "$original" =~ "구현" ]]; then
                migrated="feat(back): ${original}"
            elif [[ "$original" =~ "수정" ]]; then
                migrated="fix(back): ${original}"
            else
                migrated="feat(back): ${original}"
            fi
            ;;
        
        # 프론트엔드 관련
        *"프론트"*|*"frontend"*|*"front"*)
            if [[ "$original" =~ "리팩터링" ]]; then
                migrated="refactor(front): ${original}"
            elif [[ "$original" =~ "구현" ]]; then
                migrated="feat(front): ${original}"
            elif [[ "$original" =~ "수정" ]]; then
                migrated="fix(front): ${original}"
            else
                migrated="feat(front): ${original}"
            fi
            ;;
        
        # Phase 패턴
        *"phase"*|*"Phase"*)
            if [[ "$original" =~ "front" ]]; then
                migrated="refactor(front): ${original}"
            elif [[ "$original" =~ "back" ]]; then
                migrated="refactor(back): ${original}"
            else
                migrated="refactor(core): ${original}"
            fi
            ;;
        
        # 기본값: 내용을 분석해서 추론
        *)
            if [[ "$original" =~ "추가"|"구현"|"생성"|"완료" ]]; then
                migrated="feat(core): ${original}"
            elif [[ "$original" =~ "수정"|"해결"|"오류"|"버그" ]]; then
                migrated="fix(core): ${original}"
            elif [[ "$original" =~ "리팩터링"|"개선"|"최적화" ]]; then
                migrated="refactor(core): ${original}"
            elif [[ "$original" =~ "테스트" ]]; then
                migrated="test(unit): ${original}"
            elif [[ "$original" =~ "문서"|"가이드"|"README" ]]; then
                migrated="docs(readme): ${original}"
            else
                migrated="chore(misc): ${original}"
            fi
            ;;
    esac
    
    echo "$migrated"
}

# 메인 마이그레이션 함수
main() {
    log_info "커밋 히스토리 마이그레이션 시작"
    
    # 작업 디렉터리 확인
    if [[ ! -d ".git" ]]; then
        log_error "Git 저장소가 아닙니다. 저장소 루트에서 실행해주세요."
        exit 1
    fi
    
    # 백업 확인
    log_warning "⚠️  이 작업은 Git 히스토리를 영구적으로 변경합니다!"
    echo "계속하기 전에 다음을 확인하세요:"
    echo "1. 백업이 생성되었는지 확인"
    echo "2. 다른 팀원들과 협의했는지 확인"
    echo "3. 원격 저장소 푸시 전 충분한 테스트"
    echo ""
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "마이그레이션 취소됨"
        exit 0
    fi
    
    # 현재 브랜치 확인
    current_branch=$(git branch --show-current)
    log_info "현재 브랜치: $current_branch"
    
    # 임시 브랜치 생성
    temp_branch="migration-temp-$(date +%s)"
    git checkout -b "$temp_branch"
    log_info "임시 브랜치 생성: $temp_branch"
    
    # git filter-branch를 사용한 커밋 메시지 변경
    log_info "커밋 메시지 마이그레이션 실행..."
    
    # 마이그레이션 함수를 환경에 export
    export -f migrate_commit_message
    
    git filter-branch --msg-filter '
        migrated=$(migrate_commit_message "$1")
        echo "$migrated"
    ' -- --all
    
    log_success "마이그레이션 완료!"
    
    # 결과 확인
    log_info "마이그레이션 결과 확인 (최근 10개 커밋):"
    git log --oneline -10
    
    echo ""
    log_info "다음 단계:"
    echo "1. git log로 결과 확인"
    echo "2. 테스트 실행: docker-compose exec backend pytest tests/"
    echo "3. 만족하면 원본 브랜치로 병합: git checkout $current_branch && git merge $temp_branch"
    echo "4. 임시 브랜치 삭제: git branch -d $temp_branch"
    echo "5. 원격 저장소에 강제 푸시: git push --force-with-lease origin $current_branch"
    
    log_warning "주의: 원격 저장소 푸시 전 팀원들과 꼭 협의하세요!"
}

# 스크립트 실행
main "$@"
