import csv, json, urllib.request, urllib.error

bad = []
for r in csv.DictReader(open("db/seeded-users.csv")):
    body = json.dumps({"username": r["username"], "password": r["password"]}).encode()
    req = urllib.request.Request("http://127.0.0.1:8080/login", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        code = urllib.request.urlopen(req).status
    except urllib.error.HTTPError as e:
        code = e.code
    if code != int(r["expected"]):
        bad.append((r["username"], r["expected"], code))
print(len(bad), "mismatches")
for b in bad:
    print(b)