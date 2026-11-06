#!/usr/bin/env python3
"""인천공항 공식 API(공공데이터포털)에서 그날 다카마쓰 가는 편(출발)·오는 편(인천 도착)을 편명과 상관없이 받아 status.json 으로 저장.
매일 오늘 날짜 자료를 띄운다. 평소 15분마다, 여행 당일(1/19 가는 편, 1/22 오는 편)은 5분마다. 1/23까지.
키는 GitHub Secret INCHEON_API_KEY 로만 쓰고 파일에는 남기지 않는다."""
import json, os, sys, urllib.parse, urllib.request, datetime as dt

KEY = os.environ.get("INCHEON_API_KEY", "")
BASE = "https://apis.data.go.kr/B551177/statusOfAllFltDeOdp/"
KST = dt.timezone(dt.timedelta(hours=9))
def D(y, m, d, h=0, mi=0): return dt.datetime(y, m, d, h, mi, tzinfo=KST)
END = D(2027, 1, 23, 23, 59)
SECTIONS = [  # (이름, 오퍼레이션, 여행 당일)
    ("dep", "getFltDeparturesDeOdp", "20270119"),
    ("arr", "getFltArrivalsDeOdp", "20270122"),
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "status.json")

def iso(s):
    s = (s or "").strip()
    if len(s) >= 12 and s[:12].isdigit():
        return "%s-%s-%sT%s:%s:00+09:00" % (s[0:4], s[4:6], s[6:8], s[8:10], s[10:12])
    return ""

def call(op, day):
    # 편명과 상관없이 다카마쓰(TAK)로 거른다(확인용 호출에서 airportCode 로 걸러짐을 확인함)
    q = {"serviceKey": KEY, "type": "json", "searchdtCode": "S", "searchDate": day, "airportCode": "TAK",
         "searchFrom": "0000", "searchTo": "2400", "passengerOrCargo": "P", "numOfRows": "50", "pageNo": "1"}
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

def age_of(sec):
    try:
        return (dt.datetime.now(KST) - dt.datetime.fromisoformat(sec.get("updated", ""))).total_seconds()
    except Exception:
        return 1e9

def main():
    now = dt.datetime.now(KST)
    force = "--force" in sys.argv
    old = {}
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        pass
    new, changed = dict(old), False
    if now > END and not force:
        print("여행 끝남:", now.isoformat()); return
    today = now.strftime("%Y%m%d")
    for name, op, trip in SECTIONS:
        prev = old.get(name) if isinstance(old.get(name), dict) else {}
        age = age_of(prev)
        # 여행 당일이면 5분마다, 평소엔 15분마다(cron 은 5분마다 도니 분이 0~4 일 때만)
        if today != trip and now.minute % 15 >= 5 and not force:
            continue
        if not KEY:
            print("INCHEON_API_KEY 없음"); continue
        try:
            flights = {}
            for i in items(call(op, today)):
                if pick(i, "codeshare").lower() == "slave":   # 공동운항 중복 줄은 뺀다
                    continue
                fid = pick(i, "flightId")
                if not fid:
                    continue
                f = {"airline": pick(i, "airline"), "sched": iso(pick(i, "scheduleDateTime")),
                     "est": iso(pick(i, "estimatedDateTime")), "remark": pick(i, "remark"),
                     "gate": pick(i, "gateNumber"), "terminal": pick(i, "terminalId")}
                if name == "dep":
                    f["counter"] = pick(i, "chkinRange")
                else:
                    f["belt"] = pick(i, "carousel"); f["exit"] = pick(i, "exitNumber")
                flights[fid] = f
        except Exception as e:
            print(name, "호출 실패:", type(e).__name__); continue
        # 내용이 같아도 25분마다는 갱신 시각을 새로 적는다(사이트는 3시간 넘은 자료를 숨김)
        if prev.get("flights") == flights and prev.get("date") == now.strftime("%Y-%m-%d") and age < 25 * 60:
            print(name, "변화 없음"); continue
        new[name] = {"updated": now.isoformat(timespec="seconds"), "date": now.strftime("%Y-%m-%d"), "flights": flights}
        changed = True
        print(name, "저장:", json.dumps(flights, ensure_ascii=False))
    new.pop("updated", None); new.pop("flights", None)   # 옛 형식 정리
    if changed or old != new:
        json.dump(new, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

main()
