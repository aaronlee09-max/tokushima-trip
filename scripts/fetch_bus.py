#!/usr/bin/env python3
"""경기도 버스위치정보 API로 8-1번 버스가 내 정류장까지 몇 정류장 남았는지 bus_status.json 에 저장.
1/19 아침(07:30~10:30 일본·한국 시각)에만 돌고, 수동 실행에서 FORCE=true 면 언제든 돈다."""
import json, os, urllib.error, urllib.parse, urllib.request, datetime as dt

KEY = os.environ.get("INCHEON_API_KEY", "")
FORCE = os.environ.get("FORCE", "").lower() == "true"
ROUTE_ID = "208000010"   # 안양 8-1번
TARGET_SEQ = 33          # 「오뚜기식품.두산벤처다임」 인덕원 방향 정류장 순서
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus_status.json")
KST = dt.timezone(dt.timedelta(hours=9))

def main():
    now = dt.datetime.now(KST)
    s, e = dt.datetime(2027, 1, 19, 7, 30, tzinfo=KST), dt.datetime(2027, 1, 19, 10, 30, tzinfo=KST)
    if not (s <= now <= e) and not FORCE:
        print("실행 시간대 밖:", now.isoformat()); return
    if not KEY:
        print("INCHEON_API_KEY 없음"); return
    q = {"serviceKey": KEY, "format": "json", "routeId": ROUTE_ID}
    url = "https://apis.data.go.kr/6410000/buslocationservice/v2/getBusLocationListv2?" + urllib.parse.urlencode(q, safe="%")
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        print("호출 실패:", type(ex).__name__); return
    body = (data.get("response") or {}).get("msgBody") or {}
    lst = body.get("busLocationList") or []
    if isinstance(lst, dict): lst = [lst]
    buses = []
    for b in lst:
        try: seq = int(b.get("stationSeq"))
        except Exception: continue
        if 0 < seq <= TARGET_SEQ:   # 내 정류장 앞쪽(같은 방향)에 있는 버스
            buses.append({"d": TARGET_SEQ - seq, "seat": b.get("remainSeatCnt"), "state": b.get("stateCd")})
    buses.sort(key=lambda x: x["d"])
    out = {"updated": now.isoformat(timespec="seconds"), "route": "8-1", "target": TARGET_SEQ, "buses": buses[:5]}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", json.dumps(out["buses"], ensure_ascii=False))

main()
