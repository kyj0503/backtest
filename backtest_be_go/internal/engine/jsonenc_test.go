package engine

import (
	"encoding/json"
	"math"
	"math/rand/v2"
	"testing"
)

// 빠른 인코더의 숫자·문자열 형식이 표준 encoding/json(SetEscapeHTML(false))과 같아야 한다.
func TestFastEncoderMatchesEncodingJSON(t *testing.T) {
	floats := []float64{0, math.Copysign(0, -1), 1, -1, 0.1, 1e-6, 9.99999e-7, 1e-7, 1.5e-12, 1e20, 1e21, 1.234e21, 123456789.123456789,
		-2.5e-9, 100, 1.0 / 3, math.MaxFloat64, math.SmallestNonzeroFloat64, 4.9e-324, 7.17e-7}
	r := rand.New(rand.NewPCG(1, 2))
	for range 20000 {
		floats = append(floats, math.Float64frombits(r.Uint64()&^(0x7ff<<52)|uint64(r.IntN(2046)+1)<<52))
	}
	for _, f := range floats {
		w := &jw{}
		w.float(f)
		want, _ := marshalNoEscape(f)
		if string(w.b) != string(want) {
			t.Fatalf("float %v: got %s want %s", f, w.b, want)
		}
	}
	strs := []string{"", "plain", "예금__cash_1", `quote " back \ slash`, "<&>", "tab\tnl\ncr\r", "\x00\x01\x08\x0c\x1f\x7f",
		"  ", "bad\xffutf8", "\xc3\x28", "emoji 😀", "λ", "_sma_help…(C,10)"}
	for _, s := range strs {
		w := &jw{}
		w.str(s)
		want, _ := marshalNoEscape(s)
		if string(w.b) != string(want) {
			t.Fatalf("string %q: got %s want %s", s, w.b, want)
		}
	}
	w := &jw{}
	w.float(math.NaN())
	if w.err == nil {
		t.Fatal("NaN must be an encoding error")
	}
}

func TestOrderedSetAndAppend(t *testing.T) {
	var o Ordered[int]
	for i := range 40 {
		o.Set(string(rune('A'+i)), i)
	}
	o.Set("C", 100)
	if v, _ := o.Get("C"); v != 100 || o.Len() != 40 {
		t.Fatal(v, o.Len())
	}
	if v, ok := o.Get("e"); !ok || v != 36 {
		t.Fatal(v, ok)
	}
	raw, _ := json.Marshal(Ordered[int]{keys: []string{"b", "a"}, vals: []int{1, 2}})
	if string(raw) != `{"b":1,"a":2}` {
		t.Fatal(string(raw))
	}
}
