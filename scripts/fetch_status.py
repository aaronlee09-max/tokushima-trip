#!/usr/bin/env python3
"""인천공항 공식 API(공공데이터포털)에서 LJ299/LJ300 운항 상태를 받아 status.json 으로 저장.
키는 GitHub Secret INCHEON_API_KEY 로만 쓰고 파일에는 남기지 않는다."""
import json, os, sys, urllib.parse, urllib.request, datetime as dt

KEY = os.environ.get("INCHEON_API_KEY", "")
BASE = "https://apis.data.go.kr/B551177/statusOfAllFltDeOdp/"
JST = dt.timezone(dt.timedelta(hours=9))
# 호출 한도(개발 계정 하루 500건)를 지키려고 필요한 시간대에만 부른다.
def T(y, m, d, h, mi): return dt.datetime(y, m, d, h, mi, tzinfo=dt.timezone(dt.timedelta(hours=9)))
TARGETS = [  # (표시 이름, 편명, 오퍼레이션, 날짜, 조회 시작, 조회 끝) — 다카마쓰로 가는 LJ299만
    # 인천 API는 조회일 기준 -3일~+6일만 주므로 1/12부터 조회가 의미 있다.
    ("LJ299", "LJ299", "getFltDeparturesDeOdp", "20270119", T(2027, 1, 12, 0, 0), T(2027, 1, 19, 23, 59)),
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
    force = "--force" in sys.argv
    active = [t for t in TARGETS if t[4] <= now <= t[5] or force]
    # 당일(1/19)은 5분마다, 그 전날들은 하루 종일 1시간에 한 번만 조회(호출량 절약)
    try:
        _prev = json.load(open(OUT, encoding="utf-8")).get("updated", "")
        _age = (now - dt.datetime.fromisoformat(_prev)).total_seconds()
    except Exception:
        _age = 1e9
    if now.date() < dt.date(2027, 1, 19) and _age < 55 * 60 and not force:
        print("전날까지는 1시간에 한 번:", int(_age // 60), "분 전에 조회"); return
    if not active:
        print("조회 시간대 밖:", now.isoformat()); return
    if not KEY:
        print("INCHEON_API_KEY 없음"); sys.exit(0)
    old = {}
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        pass
    flights = dict(old.get("flights") or {})
    for name, flight, op, day, _s, _e in active:
        try:
            lst = [i for i in items(call(op, flight, day)) if pick(i, "flightId", "flightid") == flight]
            if not lst:
                flights[name] = {"error": "해당 편 정보 없음"}; continue
            i = lst[0]
            flights[name] = {
                "sched": iso(pick(i, "scheduleDateTime")), "est": iso(pick(i, "estimatedDateTime")),
                "remark": pick(i, "remark"), "gate": pick(i, "gateNumber"),
                "counter": pick(i, "chkinRange"), "terminal": pick(i, "terminalId"),
                "belt": pick(i, "carousel"), "exit": pick(i, "exitNumber")}
        except Exception as e:
            flights[name] = {"error": type(e).__name__}
    out = {"updated": now.isoformat(timespec="seconds"), "flights": flights}
    # 내용이 같아도 25분마다는 갱신 시각을 새로 적어 둔다(사이트는 1시간 넘은 자료를 숨기기 때문)
    try:
        age = (now - dt.datetime.fromisoformat(old.get("updated", ""))).total_seconds()
    except Exception:
        age = 1e9
    if old.get("flights") == flights and age < 25 * 60:
        print("변화 없음"); return
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", json.dumps(flights, ensure_ascii=False))

main()
