#!/usr/bin/env python3
"""경기도 버스 API 시험 호출: 8842 노선 ID, 정류장 목록, 현재 버스 위치를 로그로 출력한다.
키는 환경변수 INCHEON_API_KEY(같은 공공데이터포털 키)를 쓰고, 출력에는 키를 찍지 않는다."""
import json, os, urllib.error, urllib.parse, urllib.request

KEY = os.environ.get("INCHEON_API_KEY", "")
ROOT = "https://apis.data.go.kr/6410000/"

def get(path, **q):
    q = dict(q, serviceKey=KEY, format="json")
    url = ROOT + path + "?" + urllib.parse.urlencode(q, safe="%")
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            txt = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:300].replace(KEY, "***")
        except Exception:
            pass
        return {"_error": "HTTPError", "_code": e.code, "_body": body}
    except Exception as e:
        return {"_error": type(e).__name__}
    try:
        return json.loads(txt)
    except Exception:
        return {"_raw": txt[:600].replace(KEY, "***")}

def show(title, obj, n=1800):
    print("\n=== " + title + " ===")
    print(json.dumps(obj, ensure_ascii=False, indent=1)[:n].replace(KEY, "***"))

def find(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key: return v
            r = find(v, key)
            if r is not None: return r
    if isinstance(o, list):
        for v in o:
            r = find(v, key)
            if r is not None: return r
    return None

if not KEY:
    print("INCHEON_API_KEY 없음"); raise SystemExit
print("\n=== 서비스별 접근 점검 ===")
for name, path, q in [("노선조회", "busrouteservice/v2/getBusRouteListv2", {"keyword": "8842"}),
                      ("버스위치", "buslocationservice/v2/getBusLocationListv2", {"routeId": "0"}),
                      ("도착정보", "busarrivalservice/v2/getBusArrivalListv2", {"stationId": "0"})]:
    r = get(path, **q)
    print(name, "→", json.dumps(r, ensure_ascii=False)[:250].replace(KEY, "***"))
print("\n=== 8-1번(routeId 208000010) 위치 ===")
r81 = get("buslocationservice/v2/getBusLocationListv2", routeId="208000010")
print(json.dumps(r81, ensure_ascii=False, indent=1)[:2500].replace(KEY, "***"))
routes = get("busrouteservice/v2/getBusRouteListv2", keyword="8842")
show("노선 검색(8842)", routes)
lst = find(routes, "busRouteList")
if isinstance(lst, dict): lst = [lst]
for r in (lst or [])[:3]:
    rid = r.get("routeId")
    if not rid: continue
    print("\n--- routeId", rid, r.get("routeName"), r.get("regionName"), "---")
    st = get("busrouteservice/v2/getBusRouteStationListv2", routeId=rid)
    items = find(st, "busRouteStationList")
    if isinstance(items, list):
        print("정류장 수:", len(items))
        for s in items:
            nm = s.get("stationName", "")
            if any(w in nm for w in ("청사", "과천", "사당", "김포", "인천", "남태령", "광주")):
                print({k: s.get(k) for k in ("stationSeq", "stationId", "stationName", "turnYn")})
    else:
        show("정류장 목록", st, 800)
    loc = get("buslocationservice/v2/getBusLocationListv2", routeId=rid)
    show("현재 버스 위치", loc, 1500)
