package config

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"math/big"
	"net"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestDatabaseURLInSQLAlchemyForm(t *testing.T) {
	db, err := loadDatabase(env(map[string]string{
		"DATABASE_URL": "mysql+pymysql://app%40user:p%40ss:word@db.internal:3307/stock_data_cache?charset=utf8mb4",
	}))
	if err != nil {
		t.Fatal(err)
	}
	if db.Host != "db.internal" || db.Port != 3307 || db.User != "app@user" || db.Password != "p@ss:word" ||
		db.Name != "stock_data_cache" || db.Charset != "utf8mb4" || db.TLSCAFile != "" {
		t.Fatalf("unexpected %+v", db)
	}
	cfg, err := db.DriverConfig(0)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Addr != "db.internal:3307" || cfg.User != "app@user" || cfg.Passwd != "p@ss:word" || cfg.ParseTime {
		t.Fatalf("unexpected driver config %+v", cfg)
	}
	// Params의 항목은 드라이버가 `SET <name>=...` 시스템 변수로 보낸다. charset이 거기 있으면
	// MySQL이 Error 1193으로 접속을 거부한다(실제 MySQL 스모크 테스트에서 발견).
	if _, ok := cfg.Params["charset"]; ok {
		t.Fatal("charset must not be sent as a system variable")
	}
	if cfg.Params["time_zone"] != "'+00:00'" {
		t.Fatalf("session time zone must be UTC, got %q", cfg.Params["time_zone"])
	}
	if dsn := cfg.FormatDSN(); !strings.Contains(dsn, "charset=utf8mb4") {
		t.Fatalf("connection charset lost: %s", dsn)
	}
	if strings.Contains(db.Redacted(), "p@ss") {
		t.Fatal("redacted summary leaked the password")
	}
}

func TestDatabaseComponentsWhenURLMissing(t *testing.T) {
	db, err := loadDatabase(env(map[string]string{
		"DATABASE_HOST": "mysql", "DATABASE_PORT": "3306", "DATABASE_USER": "u",
		"DATABASE_PASSWORD": "p", "DATABASE_NAME": "stock_data_cache",
	}))
	if err != nil {
		t.Fatal(err)
	}
	if db.Host != "mysql" || db.User != "u" || db.Password != "p" || db.Name != "stock_data_cache" {
		t.Fatalf("unexpected %+v", db)
	}
}

func TestDatabaseTLSFromIndividualVariables(t *testing.T) {
	db, err := loadDatabase(env(map[string]string{
		"DATABASE_HOST": "10.0.0.5", "DATABASE_USER": "u", "DATABASE_SSL_CA": "/app/tls/ca.pem",
		"DATABASE_SSL_CHECK_HOSTNAME": "false",
	}))
	if err != nil {
		t.Fatal(err)
	}
	if db.TLSCAFile != "/app/tls/ca.pem" || db.TLSCheckHostname || !db.Configured {
		t.Fatalf("%+v", db)
	}
	if !strings.Contains(db.Redacted(), "tls=verify-ca") {
		t.Fatal(db.Redacted())
	}
}

func TestDatabaseURLRejectsUnknownOrBrokenParameters(t *testing.T) {
	for _, raw := range []string{
		"postgres://u:p@h/db",
		"mysql://u:p@h/",
		"mysql://u:p@h/db?ssl_mode=REQUIRED", // 오타·미지원 TLS 옵션이 평문 접속으로 이어지면 안 된다
		"mysql://u:p@h/db?ssl_check_hostname=nope",
		"mysql://u:p@h:port/db",
	} {
		if _, err := loadDatabase(env(map[string]string{"DATABASE_URL": raw})); err == nil {
			t.Errorf("%s: expected error", raw)
		} else if strings.Contains(err.Error(), ":p@") {
			t.Errorf("%s: error leaked credentials: %v", raw, err)
		}
	}
}

// OCI 관리형 MySQL 구성: 사설 CA로 체인은 검증하고 호스트명 검사만 끈다.
func TestTLSWithoutHostnameStillVerifiesChain(t *testing.T) {
	dir := t.TempDir()
	trusted := newCA(t, "trusted root")
	other := newCA(t, "other root")
	caFile := filepath.Join(dir, "ca.pem")
	if err := os.WriteFile(caFile, trusted.pem, 0o600); err != nil {
		t.Fatal(err)
	}
	db := Database{Host: "10.0.0.5", Port: 3306, Name: "db", Charset: "utf8mb4", TLSCAFile: caFile}

	cfg, err := db.tlsConfig()
	if err != nil {
		t.Fatal(err)
	}
	if !cfg.InsecureSkipVerify || cfg.VerifyConnection == nil {
		t.Fatal("hostname-less mode must replace default verification with chain verification")
	}
	// 인증서 SAN은 "mysql.oraclecloud.internal" — 접속 호스트(10.0.0.5)와 달라도 통과해야 한다.
	good := trusted.leaf(t, "mysql.oraclecloud.internal")
	if err := cfg.VerifyConnection(tls.ConnectionState{PeerCertificates: []*x509.Certificate{good}}); err != nil {
		t.Fatalf("trusted chain rejected: %v", err)
	}
	bad := other.leaf(t, "mysql.oraclecloud.internal")
	if err := cfg.VerifyConnection(tls.ConnectionState{PeerCertificates: []*x509.Certificate{bad}}); err == nil {
		t.Fatal("certificate from an untrusted CA was accepted")
	}
	if err := cfg.VerifyConnection(tls.ConnectionState{}); err == nil {
		t.Fatal("empty peer certificate list was accepted")
	}

	db.TLSCheckHostname = true
	strict, err := db.tlsConfig()
	if err != nil {
		t.Fatal(err)
	}
	if strict.InsecureSkipVerify || strict.ServerName != "10.0.0.5" {
		t.Fatalf("verify-full mode must use standard verification, got %+v", strict)
	}
}

func TestTLSRejectsMissingOrEmptyCA(t *testing.T) {
	dir := t.TempDir()
	empty := filepath.Join(dir, "empty.pem")
	if err := os.WriteFile(empty, []byte("not a certificate"), 0o600); err != nil {
		t.Fatal(err)
	}
	for _, file := range []string{filepath.Join(dir, "missing.pem"), empty} {
		db := Database{Host: "h", Port: 3306, Name: "db", TLSCAFile: file}
		if _, err := db.DriverConfig(0); err == nil {
			t.Errorf("%s: expected error", file)
		}
	}
}

type testCA struct {
	cert *x509.Certificate
	key  *ecdsa.PrivateKey
	pem  []byte
}

func newCA(t *testing.T, name string) testCA {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	tmpl := &x509.Certificate{
		SerialNumber:          big.NewInt(1),
		Subject:               pkix.Name{CommonName: name},
		NotBefore:             time.Now().Add(-time.Hour),
		NotAfter:              time.Now().Add(time.Hour),
		IsCA:                  true,
		KeyUsage:              x509.KeyUsageCertSign,
		BasicConstraintsValid: true,
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	cert, err := x509.ParseCertificate(der)
	if err != nil {
		t.Fatal(err)
	}
	return testCA{cert: cert, key: key, pem: pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})}
}

func (ca testCA) leaf(t *testing.T, dnsName string) *x509.Certificate {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(2),
		Subject:      pkix.Name{CommonName: dnsName},
		DNSNames:     []string{dnsName},
		IPAddresses:  []net.IP{net.ParseIP("192.0.2.1")},
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, ca.cert, &key.PublicKey, ca.key)
	if err != nil {
		t.Fatal(err)
	}
	cert, err := x509.ParseCertificate(der)
	if err != nil {
		t.Fatal(err)
	}
	return cert
}
