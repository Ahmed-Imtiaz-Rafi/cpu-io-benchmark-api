import csv
import os
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
            p.cpu_percent(None)
        return p
    except psutil.Error:
        return None


def top_other(skip):
    best = ("", 0.0)
    for p in psutil.process_iter(["name"]):
        if p.pid in skip or p.pid == 0:
            continue
        try:
            c = p.cpu_percent(None)
        except psutil.Error:
            continue
        if c > best[1]:
            best = (p.info["name"], c)
    return best


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
    header += ["other_name", "other_cpu"]
    w.writerow(header)
    psutil.cpu_percent(None)
    top_other({os.getpid()})
    try:
        while True:
            if targets["jmeter"] is None:
                targets["jmeter"] = attach(pid_by_cmdline("ApacheJMeter", " -n "))
            time.sleep(1)
            row = [int(time.time() * 1000), psutil.cpu_percent(None),
                   psutil.virtual_memory().percent]
            skip = {os.getpid()}
            for p in targets.values():
                try:
                    row += [p.cpu_percent(None), p.memory_info().rss // 1048576]
                    skip.add(p.pid)
                except (psutil.Error, AttributeError):
                    row += ["", ""]
            row += list(top_other(skip))
            w.writerow(row)
            f.flush()
    except KeyboardInterrupt:
        pass