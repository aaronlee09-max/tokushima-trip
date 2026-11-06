#!/usr/bin/env python3
"""10164 정류소를 지나는 노선 중, 정부과천청사·인덕원역 정류소에도 서는 노선을 찾는다(키는 출력하지 않음)."""
import json, os, urllib.error, urllib.parse, urllib.request
KEY = os.environ.get("INCHEON_API_KEY", "")
ROOT = "https://apis.data.go.kr/6410000/"
def get(path, **q):
    q = dict(q, serviceKey=KEY, format="json")
    try:
        with urllib.request.urlopen(ROOT + path + "?" + urllib.parse.urlencode(q, safe="%"), timeout=25) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_error": type(e).__name__}
def find(o, k):
    if isinstance(o, dict):
        for a, v in o.items():
            if a == k: return v
            r = find(v, k)
            if r is not None: return r
    if isinstance(o, list):
        for v in o:
            r = find(v, k)
            if r is not None: return r
def lst(x):
    return [x] if isinstance(x, dict) else (x or [])
def routes(sid):
    return {str(r["routeId"]): (r.get("routeName"), r.get("staOrder"), r.get("routeDestName")) for r in lst(find(get("busstationservice/v2/getBusStationViaRouteListv2", stationId=sid), "busRouteList"))}
opp = routes(209000113)
print("10168(나눔초등학교.오뚜기식품) 경유 노선:", {v[0]: (k, v[1], v[2]) for k, v in opp.items()})
mine = opp
for kw in ("정부과천청사", "인덕원역", "인덕원"):
    ss = lst(find(get("busstationservice/v2/getBusStationListv2", keyword=kw), "busStationList"))
    print("\n=== 정류소 검색:", kw, "→", len(ss), "곳 ===")
    for s in ss[:12]:
        sid = s.get("stationId")
        rr = routes(sid)
        common = {v[0]: (k, mine[k][1], v[1]) for k, v in rr.items() if k in mine}
        print(s.get("stationName"), s.get("mobileNo"), s.get("regionName"), sid, "| 공통 노선(번호:노선ID,내순서,이곳순서):", common)
