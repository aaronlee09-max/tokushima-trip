#!/usr/bin/env python3
"""인천 출발편 API 응답 모양 확인용(키는 env 에서만, 출력에 URL·키는 남기지 않음)."""
import json, os, urllib.parse, urllib.request, datetime as dt
KEY = os.environ.get("INCHEON_API_KEY", "")
BASE = "https://apis.data.go.kr/B551177/statusOfAllFltDeOdp/getFltArrivalsDeOdp"
day = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y%m%d")
def call(extra):
    q = {"serviceKey": KEY, "type": "json", "searchdtCode": "S", "searchDate": day, "searchFrom": "0000",
         "searchTo": "2400", "passengerOrCargo": "P", "numOfRows": "1000", "pageNo": "1"}
    q.update(extra)
    url = BASE + "?" + urllib.parse.urlencode(q, safe="%")
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_err": type(e).__name__ + " " + str(e)[:80].replace(KEY, "***")}
def items(d):
    b = (d.get("response") or {}).get("body") or {}
    it = b.get("items")
    if isinstance(it, dict): it = it.get("item", [])
    if isinstance(it, dict): it = [it]
    return b, it or []
for name, extra in [("도착 필터 없음", {}), ("도착 airportCode=TAK", {"airportCode": "TAK"})]:
    d = call(extra)
    if "_err" in d: print(name, "오류:", d["_err"]); continue
    h = (d.get("response") or {}).get("header") or {}
    b, it = items(d)
    print("==", name, "| 결과코드:", h.get("resultCode"), h.get("resultMsg"), "| totalCount:", b.get("totalCount"), "| 받은 줄:", len(it))
    if it and name == "도착 필터 없음":
        print("필드:", sorted(it[0].keys()))
        print("TAK 줄 예:", json.dumps(next((i for i in it if str(i.get("airportCode","")).upper()=="TAK"), {}), ensure_ascii=False))
        print("첫 줄:", json.dumps(it[0], ensure_ascii=False))
    tak = [i for i in it if "TAK" in (str(i.get("airportCode", "")).upper(),) or "다카마쓰" in str(i.get("airport", ""))]
    print("다카마쓰행:", [(i.get("flightId"), i.get("scheduleDateTime"), i.get("remark")) for i in tak])
