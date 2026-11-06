#!/usr/bin/env python3
"""경기도 버스위치정보 API로 441·502·540·777번이 내 정류장까지 몇 정류장 남았는지 bus_status.json 에 저장.
1/19 아침(07:30~10:30 일본·한국 시각)에만 돌고, 수동 실행에서 FORCE=true 면 언제든 돈다."""
import json, os, urllib.error, urllib.parse, urllib.request, datetime as dt

KEY = os.environ.get("INCHEON_API_KEY", "")
FORCE = os.environ.get("FORCE", "").lower() == "true"
# 정류장 「나눔초등학교.오뚜기식품.두산벤처다임」(10168, stationId 209000113)을 지나가고
# 정부과천청사역에 서는 노선: (번호, 노선ID, 이 정류장의 노선 내 순서)
ROUTES = [("441", "100100070", 30), ("502", "100100410", 30), ("540", "100100083", 21), ("777", "233000007", 56)]
MAX_BEHIND = 20
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus_status.json")
KST = dt.timezone(dt.timedelta(hours=9))

def main():
    now = dt.datetime.now(KST)
    s, e = dt.datetime(2027, 1, 19, 7, 30, tzinfo=KST), dt.datetime(2027, 1, 19, 10, 30, tzinfo=KST)
    if not (s <= now <= e) and not FORCE:
        print("실행 시간대 밖:", now.isoformat()); return
    if not KEY:
        print("INCHEON_API_KEY 없음"); return
    buses = []
    for name, rid, target in ROUTES:
        q = {"serviceKey": KEY, "format": "json", "routeId": rid}
        url = "https://apis.data.go.kr/6410000/buslocationservice/v2/getBusLocationListv2?" + urllib.parse.urlencode(q, safe="%")
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as ex:
            print(name, "호출 실패:", type(ex).__name__); continue
        lst = ((data.get("response") or {}).get("msgBody") or {}).get("busLocationList") or []
        if isinstance(lst, dict): lst = [lst]
        for b in lst:
            try: seq = int(b.get("stationSeq"))
            except Exception: continue
            d = target - seq
            if 0 <= d <= MAX_BEHIND:
                buses.append({"n": name, "d": d, "seat": b.get("remainSeatCnt")})
    buses.sort(key=lambda x: x["d"])
    out = {"updated": now.isoformat(timespec="seconds"), "stop": "10168", "buses": buses[:8]}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", json.dumps(out["buses"], ensure_ascii=False))

main()
