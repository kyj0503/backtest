package config

import (
	"crypto/tls"
	"crypto/x509"
	"errors"
	"fmt"
	"net"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/go-sql-driver/mysql"
)

// Database는 MySQL 접속 설정이다. DATABASE_URL이 있으면 개별 DATABASE_* 값보다 우선한다.
//
// DATABASE_URL은 Python 시절 SQLAlchemy 형식을 그대로 받는다:
//
//	mysql+pymysql://user:pass@host:3306/stock_data_cache?charset=utf8mb4&ssl_ca=/app/tls/ca.pem&ssl_check_hostname=false
//
// 운영(OCI 관리형 MySQL)은 ssl_ca로 서버 인증서 체인을 검증하고, 인증서에 사설 호스트명이 없어서
// ssl_check_hostname=false로 호스트명 검사만 끈다. 체인 검증은 끄지 않는다.
type Database struct {
	Host     string
	Port     int
	User     string
	Password string
	Name     string
	Charset  string

	TLSCAFile        string
	TLSCheckHostname bool

	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration

	// Configured는 DATABASE_URL 또는 DATABASE_HOST가 주어졌는지다. 고정 시세(E2E) 실행은 DB 없이 돈다.
	Configured bool
}

func loadDatabase(getenv Getenv) (Database, error) {
	r := reader{getenv: getenv}
	db := Database{
		Charset:          "utf8mb4",
		TLSCheckHostname: true,
		MaxOpenConns:     r.integer("DATABASE_MAX_OPEN_CONNS", 16),
		MaxIdleConns:     r.integer("DATABASE_MAX_IDLE_CONNS", 4),
		ConnMaxLifetime:  r.seconds("DATABASE_CONN_MAX_LIFETIME_SECONDS", 3600),
	}
	_, hostSet := r.raw("DATABASE_HOST")
	_, urlSet := r.raw("DATABASE_URL")
	db.Configured = hostSet || urlSet
	if raw, ok := r.raw("DATABASE_URL"); ok {
		if err := db.parseURL(raw); err != nil {
			r.errs = append(r.errs, err)
		}
	} else {
		db.Host = r.str("DATABASE_HOST", "127.0.0.1")
		db.Port = r.integer("DATABASE_PORT", 3306)
		db.User = r.str("DATABASE_USER", "root")
		db.Password = r.str("DATABASE_PASSWORD", "")
		db.Name = r.str("DATABASE_NAME", "stock_data_cache")
	}
	if db.MaxOpenConns <= 0 || db.MaxIdleConns < 0 || db.MaxIdleConns > db.MaxOpenConns {
		r.errs = append(r.errs, errors.New("DATABASE_MAX_OPEN_CONNS must be positive and >= DATABASE_MAX_IDLE_CONNS"))
	}
	if db.Port <= 0 || db.Port > 65535 {
		r.errs = append(r.errs, fmt.Errorf("database port must be 1-65535, got %d", db.Port))
	}
	return db, errors.Join(r.errs...)
}

// parseURL은 SQLAlchemy URL을 해석한다. 모르는 쿼리 파라미터는 조용히 버리지 않고 오류로 돌려준다
// (TLS 설정 오타가 평문 접속으로 이어지면 안 된다).
func (db *Database) parseURL(raw string) error {
	u, err := url.Parse(raw)
	if err != nil {
		// url.Parse 오류 문자열에는 비밀번호가 들어 있을 수 있다.
		return errors.New("DATABASE_URL is not a valid URL")
	}
	if u.Scheme != "mysql" && !strings.HasPrefix(u.Scheme, "mysql+") {
		return fmt.Errorf("DATABASE_URL scheme must be mysql or mysql+<driver>, got %q", u.Scheme)
	}
	db.Host = u.Hostname()
	if db.Host == "" {
		return errors.New("DATABASE_URL has no host")
	}
	db.Port = 3306
	if p := u.Port(); p != "" {
		if db.Port, err = strconv.Atoi(p); err != nil {
			return fmt.Errorf("DATABASE_URL port %q is not a number", p)
		}
	}
	if u.User != nil {
		db.User = u.User.Username()
		db.Password, _ = u.User.Password()
	}
	db.Name = strings.TrimPrefix(u.Path, "/")
	if db.Name == "" {
		return errors.New("DATABASE_URL has no database name")
	}
	for key, values := range u.Query() {
		value := values[len(values)-1]
		switch key {
		case "charset":
			db.Charset = value
		case "ssl_ca":
			db.TLSCAFile = value
		case "ssl_check_hostname":
			b, err := strconv.ParseBool(value)
			if err != nil {
				return fmt.Errorf("DATABASE_URL ssl_check_hostname %q is not a boolean", value)
			}
			db.TLSCheckHostname = b
		default:
			return fmt.Errorf("DATABASE_URL has unsupported parameter %q", key)
		}
	}
	return nil
}

// Redacted는 로그에 남길 수 있는 접속 요약이다. 비밀번호는 넣지 않는다.
func (db Database) Redacted() string {
	tlsMode := "off"
	if db.TLSCAFile != "" {
		tlsMode = "verify-ca"
		if db.TLSCheckHostname {
			tlsMode = "verify-full"
		}
	}
	return fmt.Sprintf("host=%s port=%d user=%s db=%s tls=%s", db.Host, db.Port, db.User, db.Name, tlsMode)
}

// DriverConfig는 go-sql-driver/mysql 설정을 만든다. timeout은 연결·읽기·쓰기 타임아웃이며
// 0이면 드라이버 기본값을 쓴다(readiness 프로브만 짧은 값을 넘긴다).
func (db Database) DriverConfig(timeout time.Duration) (*mysql.Config, error) {
	base := mysql.NewConfig()
	base.User = db.User
	base.Passwd = db.Password
	base.Net = "tcp"
	base.Addr = net.JoinHostPort(db.Host, strconv.Itoa(db.Port))
	base.DBName = db.Name
	// charset은 Params에 넣으면 드라이버가 `SET charset=...` 시스템 변수로 보내 접속이 실패한다
	// (MySQL Error 1193). DSN 파서만 charset을 접속 문자셋으로 해석하므로 DSN을 거쳐 설정한다.
	cfg, err := mysql.ParseDSN(base.FormatDSN() + "?charset=" + url.QueryEscape(db.Charset))
	if err != nil {
		return nil, fmt.Errorf("database charset %q: %w", db.Charset, err)
	}
	// 세션 시간대를 UTC로 고정한다. TIMESTAMP 컬럼은 세션 시간대로 변환되어 읽히므로, 캐시 나이 계산
	// (data_last_update와 UTC_TIMESTAMP() 비교)이 서버 기본 시간대에 따라 몇 시간씩 틀어지면 안 된다.
	cfg.Params = map[string]string{"time_zone": "'+00:00'"}
	cfg.Loc = time.UTC
	cfg.ParseTime = false // DATE 컬럼은 문자열(YYYY-MM-DD)로 읽어 시간대 해석을 피한다
	cfg.Timeout = 10 * time.Second
	if timeout > 0 {
		cfg.Timeout, cfg.ReadTimeout, cfg.WriteTimeout = timeout, timeout, timeout
	}
	if db.TLSCAFile != "" {
		tlsConfig, err := db.tlsConfig()
		if err != nil {
			return nil, err
		}
		cfg.TLS = tlsConfig
	}
	return cfg, nil
}

func (db Database) tlsConfig() (*tls.Config, error) {
	pem, err := os.ReadFile(db.TLSCAFile)
	if err != nil {
		return nil, fmt.Errorf("read database CA %s: %w", db.TLSCAFile, err)
	}
	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(pem) {
		return nil, fmt.Errorf("database CA %s contains no PEM certificates", db.TLSCAFile)
	}
	cfg := &tls.Config{MinVersion: tls.VersionTLS12, RootCAs: roots, ServerName: db.Host}
	if db.TLSCheckHostname {
		return cfg, nil
	}
	// 호스트명만 건너뛰고 체인은 직접 검증한다. InsecureSkipVerify는 표준 검증 전체를 끄므로
	// VerifyConnection에서 같은 루트로 다시 검증해야 한다.
	cfg.InsecureSkipVerify = true
	cfg.VerifyConnection = func(state tls.ConnectionState) error {
		if len(state.PeerCertificates) == 0 {
			return errors.New("database server sent no certificate")
		}
		intermediates := x509.NewCertPool()
		for _, cert := range state.PeerCertificates[1:] {
			intermediates.AddCert(cert)
		}
		_, err := state.PeerCertificates[0].Verify(x509.VerifyOptions{
			Roots:         roots,
			Intermediates: intermediates,
			KeyUsages:     []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		})
		return err
	}
	return cfg, nil
}
