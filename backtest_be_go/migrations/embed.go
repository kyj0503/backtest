// Package migrations는 goose SQL 마이그레이션을 바이너리에 내장한다.
//
// 스키마를 바꿀 때는 새 번호의 파일을 추가하고 database/schema.sql을 같은 결과가 되도록 함께 고친 뒤
// scripts/check-schema-parity.sh로 두 경로가 같은지 확인한다. 이미 배포된 파일은 고치지 않는다.
package migrations

import "embed"

//go:embed *.sql
var FS embed.FS
