import csv
import sys
import time

import psutil


def pid_on_port(port):
    for c in psutil.net_connections(kind="tcp"):
        if c.status == psutil.CONN_LISTEN and c.laddr.port == port and c.pid:
            return c.pid
    return None


def pid_by_cmdline(*parts):
    for p in psutil.process_iter(["cmdline"]):
        try:
            cmd = " ".join(p.info["cmdline"] or [])
            if all(x in cmd for x in parts):
                return p.pid
        except psutil.Error:
            pass
    return None


def attach(pid):
    try:
        p = psutil.Process(pid) if pid else None
        if p:
            p.cpu_percent(None)  # baseline call
        return p
    except psutil.Error:
        return None


targets = {
    "api": attach(pid_on_port(8080)),
    "mysql": attach(pid_on_port(3306)),
     "jmeter": attach(pid_by_cmdline("ApacheJMeter", " -n ")),
}

out = sys.argv[1]
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    header = ["epoch_ms", "sys_cpu", "mem_pct"]
    for name in targets:
        header += [name + "_cpu", name + "_rss_mb"]
    w.writerow(header)
    psutil.cpu_percent(None)
    try:
        while True:
            if targets["jmeter"] is None:
                targets["jmeter"] = attach(pid_by_cmdline("ApacheJMeter", " -n "))
            time.sleep(1)
            row = [int(time.time() * 1000), psutil.cpu_percent(None),
                   psutil.virtual_memory().percent]
            for p in targets.values():
                try:
                    row += [p.cpu_percent(None), p.memory_info().rss // 1048576]
                except (psutil.Error, AttributeError):
                    row += ["", ""]
            w.writerow(row)
            f.flush()
    except KeyboardInterrupt:
        pass