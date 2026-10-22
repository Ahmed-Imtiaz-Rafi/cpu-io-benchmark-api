import time, psutil

for p in psutil.process_iter():
    try: p.cpu_percent(None)
    except psutil.Error: pass
time.sleep(10)
top = []
for p in psutil.process_iter(["name"]):
    try: top.append((p.cpu_percent(None), p.info["name"], p.pid))
    except psutil.Error: pass
for c, n, pid in sorted(top, reverse=True)[:8]:
    print(f"{c:6.1f}  {n}  {pid}")