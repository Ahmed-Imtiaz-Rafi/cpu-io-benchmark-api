import json
import socket
import subprocess
import sys
import time
import urllib.request

import psutil

import os
import csv

import shutil

cfg = json.load(open("scripts/driver_config.json"))


def port_free(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def start_api(build, log_path):
    gc = os.path.join(os.path.dirname(log_path), "gc.log")
    cmd = [cfg["java"], f"-Xlog:gc:file={gc}:uptime,time", "-jar", cfg["jars"][build],
           "--spring.config.additional-location=file:" + cfg["benchmark_properties"]]
    log = open(log_path, "w")
    return subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)


def wait_ready(proc):
    deadline = time.time() + cfg["startup_timeout_s"]
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/users/1/orders", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def stop_api(proc):
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()

def wait_quiet(max_wait_s=300):
    """Wait until system CPU stays under the threshold for a full window."""
    need = cfg["idle_window_s"]
    limit = cfg["idle_cpu_pct"]
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        samples = [psutil.cpu_percent(interval=1) for _ in range(need)]
        if max(samples) < limit:
            return True
    return False

def run_one(seq, scenario, users, rep, build, run_name, out_dir):
    d = os.path.join(out_dir, run_name)
    os.makedirs(d, exist_ok=True)
    if os.path.exists(os.path.join(d, "DONE")):
        return "skipped"
    if not wait_quiet():
        return "fault: gate"
    if not port_free(8080):
        return "fault: port"
    api = start_api(build, os.path.join(d, "api.log"))
    if not wait_ready(api):
        stop_api(api)
        return "fault: start"
    mon = subprocess.Popen([sys.executable, "scripts/monitor.py",
                            os.path.join(d, "monitor.csv")])
    t0 = int(time.time() * 1000)
    jm = subprocess.run([cfg["jmeter"], "-n", "-t", cfg["plans"][scenario],
                         f"-Jthreads={users}", f"-Jrampup={cfg['rampup_s']}",
                         f"-Jduration={cfg['duration_s']}",
                         "-l", os.path.join(d, "run.jtl")])
    t1 = int(time.time() * 1000)
    mon.terminate()
    stop_api(api)
    meta = {"seq": seq, "scenario": scenario, "users": users, "rep": rep,
            "build": build, "start_ms": t0, "end_ms": t1, "jmeter_exit": jm.returncode,
            "jar_sha256": cfg["jar_sha256"][build], "java": java_version()}
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2)
    if jm.returncode != 0:
        return "fault: jmeter"
    open(os.path.join(d, "DONE"), "w").close()
    return "ok"

import hashlib


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_jars():
    for build, path in cfg["jars"].items():
        if sha256(path) != cfg["jar_sha256"][build]:
            raise SystemExit(f"jar hash mismatch for {build}: {path}")


def java_version():
    r = subprocess.run([cfg["java"], "-version"], capture_output=True, text=True)
    return r.stderr.strip().splitlines()[0]

def run_batch(batch_name, start_seq=1, end_seq=None, out_root="results/final"):
    check_jars()
    out_dir = os.path.join(out_root, batch_name)
    os.makedirs(out_dir, exist_ok=True)
    log = open(os.path.join(out_dir, "batch.log"), "a")
    log.write(f"batch start {time.ctime()} | {java_version()}\n")
    rows = list(csv.DictReader(open("scripts/schedule.csv")))
    for r in rows:
        seq = int(r["seq"])
        if seq < start_seq or (end_seq and seq > end_seq):
            continue
        if os.path.exists("STOP"):
            log.write("STOP file found, ending batch\n")
            break
        status = "fault"
        for attempt in range(1, 4):
            status = run_one(seq, r["scenario"], int(r["users"]), int(r["rep"]),
                             r["build"], r["run_name"], out_dir)
            log.write(f"{time.ctime()} seq={seq} {r['run_name']} attempt={attempt} {status}\n")
            log.flush()
            if status.startswith("fault"):
                src = os.path.join(out_dir, r["run_name"])
                if os.path.exists(src):
                    dst = os.path.join(out_dir, "failed", f"{r['run_name']}_attempt{attempt}")
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.move(src, dst)
            if not status.startswith("fault"):
                break
        time.sleep(cfg["cooldown_s"])
    log.write(f"batch end {time.ctime()}\n")


if __name__ == "__main__":
    run_batch(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))