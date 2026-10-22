import re, sys
from collections import defaultdict

OFFSET = 5.2  # JMeter started about 5.2 s after JVM start in this run
b = defaultdict(lambda: [0, 0.0])
for line in open(sys.argv[1]):
    m = re.search(r"\]\[(\d+\.\d+)s\].*Pause.*?(\d+\.\d+)ms$", line.strip())
    if m:
        k = int((float(m.group(1)) - OFFSET) // 10)
        b[k][0] += 1
        b[k][1] += float(m.group(2))
for k in sorted(b):
    print(f"{k*10:>3}-{k*10+10:<3}s  pauses={b[k][0]:>3}  total={b[k][1]:7.1f} ms")