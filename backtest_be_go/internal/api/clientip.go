package api

import (
	"net"
	"net/http"
	"net/netip"
	"strings"
)

// clientKey는 클라이언트별 상한에 쓰는 키다(Python app/core/client_ip.py).
//
// 직접 연결한 상대가 신뢰하는 프록시(trusted)일 때만 X-Forwarded-For를 오른쪽부터 읽어, 신뢰 대역이
// 아닌 첫 주소를 클라이언트로 본다. 값 하나라도 IP가 아니면 헤더 전체를 무시한다(위조 방지).
// IPv6는 /64로 묶는다. 한 가입자가 보통 /64 전체를 받으므로 주소를 바꿔 상한을 피하지 못하게 한다.
func clientKey(r *http.Request, trusted []netip.Prefix) string {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		host = r.RemoteAddr
	}
	peer, err := netip.ParseAddr(host)
	if err != nil {
		return host
	}
	peer = peer.Unmap()
	client := peer
	if isTrusted(peer, trusted) {
		var hops []netip.Addr
		valid := true
		for _, header := range r.Header.Values("X-Forwarded-For") {
			for _, item := range strings.Split(header, ",") {
				ip, err := netip.ParseAddr(strings.TrimSpace(item))
				if err != nil {
					valid = false
					continue
				}
				hops = append(hops, ip.Unmap())
			}
		}
		if valid {
			for i := len(hops) - 1; i >= 0 && isTrusted(client, trusted); i-- {
				client = hops[i]
			}
		}
	}
	if client.Is6() {
		p, _ := client.Prefix(64)
		return p.String()
	}
	return client.String()
}

func isTrusted(ip netip.Addr, trusted []netip.Prefix) bool {
	for _, p := range trusted {
		if p.Contains(ip) {
			return true
		}
	}
	return false
}
