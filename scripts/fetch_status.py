#!/usr/bin/env python3
"""인천공항 공식 API(공공데이터포털)에서 LJ299/LJ300 운항 상태를 받아 status.json 으로 저장.
키는 GitHub Secret INCHEON_API_KEY 로만 쓰고 파일에는 남기지 않는다."""
import json, os, sys, urllib.parse, urllib.request, datetime as dt

KEY = os.environ.get("INCHEON_API_KEY", "")
BASE = "https://apis.data.go.kr/B551177/statusOfAllFltDeOdp/"
JST = dt.timezone(dt.timedelta(hours=9))
TARGETS = [  # (표시 이름, 편명, 오퍼레이션, 날짜)
    ("LJ299", "LJ299", "getFltDeparturesDeOdp", "20270119"),
    ("LJ300", "LJ300", "getFltArrivalsDeOdp", "20270122"),
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "status.json")

def iso(s):
    s = (s or "").strip()
    if len(s) >= 12 and s[:12].isdigit():
        return "%s-%s-%sT%s:%s:00+09:00" % (s[0:4], s[4:6], s[6:8], s[8:10], s[10:12])
    return ""

def call(op, flight, day):
    q = {"serviceKey": KEY, "type": "json", "searchdtCode": "S", "searchDate": day, "flightId": flight,
         "searchFrom": "0000", "searchTo": "2400", "passengerOrCargo": "P", "numOfRows": "20", "pageNo": "1"}
    url = BASE + op + "?" + urllib.parse.urlencode(q, safe="%")
    with urllib.request.urlopen(url, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

def items(data):
    body = (data.get("response") or {}).get("body") or {}
    it = body.get("items")
    if isinstance(it, dict):
        it = it.get("item", [])
    if isinstance(it, dict):
        it = [it]
    return it or []

def pick(d, *names):
    low = {k.lower(): v for k, v in d.items()}
    for n in names:
        if n.lower() in low and low[n.lower()] not in (None, ""):
            return str(low[n.lower()]).strip()
    return ""

def main():
    now = dt.datetime.now(JST)
    # 조회 가능 범위(D-3~D+6) 밖이면 아무것도 하지 않는다.
    first = dt.datetime(2027, 1, 12, tzinfo=JST); last = dt.datetime(2027, 1, 23, tzinfo=JST)
    if not (first <= now <= last) and "--force" not in sys.argv:
        print("조회 기간 밖:", now.isoformat()); return
    if not KEY:
        print("INCHEON_API_KEY 없음"); sys.exit(0)
    out = {"updated": now.isoformat(timespec="seconds"), "flights": {}}
    for name, flight, op, day in TARGETS:
        try:
            lst = [i for i in items(call(op, flight, day)) if pick(i, "flightId", "flightid") == flight] or items(call(op, flight, day))
            if not lst:
                out["flights"][name] = {"error": "해당 편 정보 없음"}; continue
            i = lst[0]
            out["flights"][name] = {
                "sched": iso(pick(i, "scheduleDateTime")), "est": iso(pick(i, "estimatedDateTime")),
                "remark": pick(i, "remark"), "gate": pick(i, "gatenumber"),
                "counter": pick(i, "chkinrange"), "terminal": pick(i, "terminalId"),
                "belt": pick(i, "carousel"), "exit": pick(i, "exitNumber")}
        except Exception as e:
            out["flights"][name] = {"error": type(e).__name__}
    old = None
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        pass
    if old and old.get("flights") == out["flights"]:
        print("변화 없음"); return
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", json.dumps(out["flights"], ensure_ascii=False))

main()
