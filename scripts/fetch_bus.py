#!/usr/bin/env python3
"""경기도 버스위치정보 API로 441·502·540·777번이 내 정류장까지 몇 정류장 남았는지 bus_status.json 에 저장.
매일 05:30~23:30(버스 운행 시간)에 돌고(여행 직전 1/18~1/19는 5분마다, 평소엔 15분마다, 1/19 이후는 멈춤), 수동 실행에서 FORCE=true 면 언제든 돈다."""
import json, os, urllib.error, urllib.parse, urllib.request, datetime as dt

KEY = os.environ.get("INCHEON_API_KEY", "")
FORCE = os.environ.get("FORCE", "").lower() == "true"
# 정류장 「나눔초등학교.오뚜기식품.두산벤처다임」(10168, stationId 209000113)을 지나가고
# 정부과천청사역에 서는 노선: (번호, 노선ID, 이 정류장의 노선 내 순서)
ROUTES = [("441", "100100070", 30), ("502", "100100410", 30), ("540", "100100083", 21), ("777", "233000007", 56)]
MAX_BEHIND = 20
DAILY_CAP = 950  # 경기도 API 일일 한도 1,000건보다 낮게 잡은 안전선(하루 호출 합계)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bus_status.json")
KST = dt.timezone(dt.timedelta(hours=9))

def main():
    now = dt.datetime.now(KST)
    # 5분 간격 × 4노선 × 18시간 ≈ 870건 → 일일 한도 1,000건 안
    trip = now.date() in (dt.date(2027, 1, 18), dt.date(2027, 1, 19))
    ok_day = now.date() <= dt.date(2027, 1, 19)
    ok_time = (5, 30) <= (now.hour, now.minute) <= (23, 30)
    slot = trip or now.minute % 15 < 5      # 평소엔 15분마다, 여행 직전·당일엔 5분마다
    if not (ok_day and ok_time and slot) and not FORCE:
        print("실행 시간대 밖:", now.isoformat()); return
    if not KEY:
        print("INCHEON_API_KEY 없음"); return
    # 오늘(KST) 이미 몇 번 불렀는지 bus_status.json 안에 적어 두고, 안전선을 넘으면 멈춘다
    today = now.strftime("%Y-%m-%d"); used = 0
    try:
        prev = json.load(open(OUT, encoding="utf-8")).get("calls") or {}
        if prev.get("date") == today: used = int(prev.get("n", 0))
    except Exception:
        pass
    if used + len(ROUTES) > DAILY_CAP:
        print("오늘 호출 안전선 도달:", used); return
    buses = []
    for name, rid, target in ROUTES:
        used += 1
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
    out = {"updated": now.isoformat(timespec="seconds"), "stop": "10168", "buses": buses[:8], "calls": {"date": today, "n": used}}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", json.dumps(out["buses"], ensure_ascii=False))

main()
