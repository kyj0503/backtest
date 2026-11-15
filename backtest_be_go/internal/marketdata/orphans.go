package marketdata

import (
	"context"
	"database/sql"
)

// daily_prices.stock_id는 물리 FK 없이 stocks.id를 가리키는 논리 참조다(A-10). 부모 stocks 행이 없는
// 일봉은 어떤 읽기 경로에서도 조회되지 않고 디스크만 차지한다. backtestctl check-orphans가 쓴다.

// OrphanPrices는 고아 일봉 수와 그 행들이 가리키는 서로 다른 stock_id 수다.
func OrphanPrices(ctx context.Context, db *sql.DB) (rows, stockIDs int64, err error) {
	err = db.QueryRowContext(ctx, `
		SELECT COUNT(*), COUNT(DISTINCT p.stock_id)
		FROM daily_prices p LEFT JOIN stocks s ON s.id = p.stock_id
		WHERE s.id IS NULL`).Scan(&rows, &stockIDs)
	return rows, stockIDs, err
}

// DeleteOrphanPrices는 고아 일봉을 지우고 지운 행 수를 돌려준다.
func DeleteOrphanPrices(ctx context.Context, db *sql.DB) (int64, error) {
	res, err := db.ExecContext(ctx, `
		DELETE p FROM daily_prices p LEFT JOIN stocks s ON s.id = p.stock_id
		WHERE s.id IS NULL`)
	if err != nil {
		return 0, err
	}
	return res.RowsAffected()
}
