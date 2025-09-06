#!/bin/bash

# 백테스팅 프로젝트 저장소 백업 스크립트
# 커밋 히스토리 마이그레이션 전 안전한 백업 생성

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${REPO_DIR}_backup_$(date +%Y%m%d_%H%M%S)"

echo "📦 저장소 백업 시작..."
echo "원본: $REPO_DIR"
echo "백업: $BACKUP_DIR"

# 완전한 저장소 복제 (모든 브랜치, 태그, 히스토리 포함)
cp -r "$REPO_DIR" "$BACKUP_DIR"
cd "$BACKUP_DIR"
# Git 상태 초기화
git status > /dev/null 2>&1

echo "✅ 백업 완료: $BACKUP_DIR"
echo ""
echo "복원 방법:"
echo "1. 현재 디렉터리 삭제: rm -rf $REPO_DIR"
echo "2. 백업 복사: cp -r $BACKUP_DIR $REPO_DIR"
echo "3. git remote 재설정"
