"""적합성 검사 전에 세 API의 /health/ready가 200이 될 때까지 기다린다(최대 4분)."""
import sys, time, urllib.request

for host in ["conf-go-api", "conf-rust-api", "conf-python-api"]:
    for _ in range(240):
        try:
            with urllib.request.urlopen(f"http://{host}:8000/health/ready", timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            pass
        time.sleep(1)
    else:
        sys.exit(f"{host} did not become ready")
print("all ready")
