package marketdata

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/go-sql-driver/mysql"

	"github.com/kyj0503/backtest/backtest_be_go/internal/civil"
)

// Store는 시세 캐시다. Cached가 (nil, nil)이면 캐시에 쓸 수 있는 스냅샷이 없다는 뜻이다.
type Store interface {
	Cached(ctx context.Context, symbol string, start, end civil.Date) (*History, error)
	Save(ctx context.Context, h History, start, end civil.Date) error
}

// 캐시 스냅샷 표식. 한 종목의 daily_prices 전체는 언제나 한 번의 제공업체 응답이다.
// 서로 다른 시점에 받은 수정 주가 구간을 합치지 않는다(rust-migration F05): 분할·배당 뒤에는
// 과거 수정 주가가 전부 바뀌기 때문이다. Python·Rust가 남긴 행에는 이 표식이 없어 다시 받는다.
const (
	snapshotKey     = "go_price_snapshot"
	snapshotVersion = 1
	// 이 범위 밖 값은 DECIMAL(38,18)에 넣으면 0으로 반올림되거나 넘친다. 저장하지 않는다.
	minStorablePrice = 1e-12
	maxStorablePrice = 1e19
)

type snapshot struct {
	Version int        `json:"version"`
	Start   civil.Date `json:"start"`
	End     civil.Date `json:"end"`
	Rows    int        `json:"rows"`
}

// MySQLStore는 stocks / daily_prices 테이블을 캐시로 쓴다.
type MySQLStore struct {
	DB     *sql.DB
	MaxAge time.Duration // 스냅샷 유효 시간 (기본 1시간)
}

func NewMySQLStore(db *sql.DB) *MySQLStore { return &MySQLStore{DB: db, MaxAge: time.Hour} }

// Cached는 [start, end]를 덮는 유효한 스냅샷을 읽는다. 메타데이터와 시세를 같은 REPEATABLE READ
// 읽기 전용 트랜잭션에서 읽어, 그 사이 다른 요청이 스냅샷을 교체해도 섞이지 않는다.
func (s *MySQLStore) Cached(ctx context.Context, symbol string, start, end civil.Date) (*History, error) {
	tx, err := s.DB.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelRepeatableRead, ReadOnly: true})
	if err != nil {
		return nil, err
	}
	defer func() { _ = tx.Rollback() }()

	var (
		id             int64
		name, exchange sql.NullString
		infoRaw        []byte
		age            sql.NullInt64
	)
	err = tx.QueryRowContext(ctx, `
		SELECT id, name, exchange, info_json, TIMESTAMPDIFF(SECOND, data_last_update, UTC_TIMESTAMP())
		FROM stocks WHERE ticker = ?`, symbol).Scan(&id, &name, &exchange, &infoRaw, &age)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	info := map[string]json.RawMessage{}
	if len(infoRaw) > 0 {
		if err := json.Unmarshal(infoRaw, &info); err != nil {
			return nil, nil // 손상된 메타데이터: 캐시로 쓰지 않고 다시 받는다
		}
	}
	var snap snapshot
	if raw, ok := info[snapshotKey]; !ok || json.Unmarshal(raw, &snap) != nil || snap.Version != snapshotVersion {
		return nil, nil
	}
	if !age.Valid || age.Int64 < 0 || time.Duration(age.Int64)*time.Second >= s.MaxAge ||
		snap.Start > start || snap.End < end {
		return nil, nil
	}

	rows, err := tx.QueryContext(ctx, `
		SELECT date, open, high, low, close, volume, data_quality
		FROM daily_prices WHERE stock_id = ? ORDER BY date`, id)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var bars []Bar
	usable := true
	for rows.Next() {
		var date, open, high, low, closeP, quality string
		var volume sql.NullInt64
		if err := rows.Scan(&date, &open, &high, &low, &closeP, &volume, &quality); err != nil {
			return nil, err
		}
		b, err := parseRow(date, open, high, low, closeP, volume)
		if err != nil || quality != "good" || !b.ValidFor(symbol) {
			usable = false // 끝까지 읽어 커넥션을 정상 반환한다
			continue
		}
		bars = append(bars, b)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	if err := tx.Commit(); err != nil {
		return nil, err
	}
	// 행이 지워졌거나 의심 표시된 스냅샷은 통째로 다시 받는다.
	if !usable || len(bars) != snap.Rows {
		return nil, nil
	}
	h := History{
		Symbol:      symbol,
		Currency:    jsonString(info["currency"]),
		CompanyName: firstNonEmpty(name.String, symbol),
		Exchange:    exchange.String,
		Bars:        bars,
	}
	if d, ok := listingDate(info); ok {
		h.FirstTradeDate = &d
	}
	h = h.Between(start, end)
	if len(h.Bars) == 0 {
		return nil, nil
	}
	return &h, nil
}

func parseRow(date, open, high, low, closeP string, volume sql.NullInt64) (Bar, error) {
	d, err := civil.Parse(date)
	if err != nil {
		return Bar{}, err
	}
	var v [4]float64
	for i, s := range []string{open, high, low, closeP} {
		if v[i], err = strconv.ParseFloat(s, 64); err != nil {
			return Bar{}, err
		}
	}
	return Bar{Date: d, Open: v[0], High: v[1], Low: v[2], Close: v[3], Volume: float64(volume.Int64)}, nil
}

func jsonString(raw json.RawMessage) string {
	var s string
	if json.Unmarshal(raw, &s) != nil {
		return ""
	}
	return s
}

// listingDate는 info_json의 상장일이다. Go가 쓰는 first_trade_date(YYYY-MM-DD)를 먼저 보고,
// Python(yfinance info)이 남긴 firstTradeDateEpochUtc(초)도 읽는다.
func listingDate(info map[string]json.RawMessage) (civil.Date, bool) {
	if d, err := civil.Parse(jsonString(info["first_trade_date"])); err == nil {
		return d, true
	}
	var epoch int64
	if raw, ok := info["firstTradeDateEpochUtc"]; ok && json.Unmarshal(raw, &epoch) == nil {
		return civil.Of(time.Unix(epoch, 0).UTC()), true
	}
	return 0, false
}

// Save는 종목의 스냅샷을 원자적으로 교체한다: 기존 일봉을 지우고 새 응답 전체를 넣는다.
// 실패하면 트랜잭션 전체가 되돌려져 기존 스냅샷이 남는다. 같은 종목의 동시 교체는 stocks 행
// 잠금(FOR UPDATE)으로 직렬화하고, 교착(1213)이 나면 몇 번 다시 시도한다.
func (s *MySQLStore) Save(ctx context.Context, h History, start, end civil.Date) error {
	for _, b := range h.Bars {
		for _, v := range []float64{b.Open, b.High, b.Low, b.Close} {
			if v < minStorablePrice || v >= maxStorablePrice {
				return fmt.Errorf("%s %s: price %g is outside the storable DECIMAL(38,18) range", h.Symbol, b.Date, v)
			}
		}
	}
	var err error
	for attempt := 0; attempt < 3; attempt++ {
		if err = s.save(ctx, h, start, end); !isDeadlock(err) {
			return err
		}
	}
	return err
}

func isDeadlock(err error) bool {
	var me *mysql.MySQLError
	return errors.As(err, &me) && (me.Number == 1213 || me.Number == 1205)
}

func (s *MySQLStore) save(ctx context.Context, h History, start, end civil.Date) error {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()

	var priorID int64
	err = tx.QueryRowContext(ctx, `SELECT id FROM stocks WHERE ticker = ? FOR UPDATE`, h.Symbol).Scan(&priorID)
	switch {
	case errors.Is(err, sql.ErrNoRows):
	case err != nil:
		return err
	default:
		if _, err := tx.ExecContext(ctx, `DELETE FROM daily_prices WHERE stock_id = ?`, priorID); err != nil {
			return err
		}
	}

	info := map[string]any{
		"currency":  h.Currency,
		"symbol":    h.Symbol,
		"shortName": h.CompanyName,
		"exchange":  h.Exchange,
		snapshotKey: snapshot{Version: snapshotVersion, Start: start, End: end, Rows: len(h.Bars)},
	}
	if h.FirstTradeDate != nil {
		info["first_trade_date"] = h.FirstTradeDate.String()
		info["firstTradeDateEpochUtc"] = h.FirstTradeDate.Time().Unix()
	}
	infoJSON, err := json.Marshal(info)
	if err != nil {
		return err
	}
	// VALUES() 함수는 MySQL 8.0.20부터 폐기 예정이라 행 별칭(AS new)을 쓴다(8.0.19+).
	if _, err := tx.ExecContext(ctx, `
		INSERT INTO stocks (ticker, name, exchange, info_json, last_info_update, data_last_update)
		VALUES (?, ?, ?, ?, UTC_TIMESTAMP(), UTC_TIMESTAMP()) AS new
		ON DUPLICATE KEY UPDATE
			name = new.name, exchange = new.exchange,
			info_json = JSON_MERGE_PATCH(COALESCE(stocks.info_json, JSON_OBJECT()), new.info_json),
			last_info_update = UTC_TIMESTAMP(), data_last_update = UTC_TIMESTAMP()`,
		h.Symbol, truncate(h.CompanyName, 255), truncate(h.Exchange, 20), infoJSON); err != nil {
		return err
	}
	var id int64
	if err := tx.QueryRowContext(ctx, `SELECT id FROM stocks WHERE ticker = ?`, h.Symbol).Scan(&id); err != nil {
		return err
	}

	const chunk = 500
	for i := 0; i < len(h.Bars); i += chunk {
		part := h.Bars[i:min(i+chunk, len(h.Bars))]
		var q strings.Builder
		q.WriteString(`INSERT INTO daily_prices (stock_id, date, open, high, low, close, adj_close, volume) VALUES `)
		args := make([]any, 0, len(part)*8)
		for j, b := range part {
			if j > 0 {
				q.WriteByte(',')
			}
			q.WriteString("(?,?,?,?,?,?,?,?)")
			// adj_close는 close와 같다: OHLC가 이미 수정 주가다.
			args = append(args, id, b.Date.String(), decimal(b.Open), decimal(b.High), decimal(b.Low),
				decimal(b.Close), decimal(b.Close), uint64(max(b.Volume, 0)))
		}
		if _, err := tx.ExecContext(ctx, q.String(), args...); err != nil {
			return err
		}
	}
	return tx.Commit()
}

// decimal은 지수 표기 없이 쓴다. MySQL이 DECIMAL(38,18)로 반올림한다.
func decimal(v float64) string { return strconv.FormatFloat(v, 'f', -1, 64) }

func truncate(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}
