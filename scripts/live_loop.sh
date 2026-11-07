#!/usr/bin/env bash
# 예약 실행(cron)은 GitHub 사정으로 몇 시간씩 밀리므로, 한 번 시작하면 약 55분 동안 5분 간격으로 직접 반복한다.
# 각 회차는 fetch_status.py / fetch_bus.py 가 알아서 "지금 받을 때인지" 판단한다(평소 15분, 여행 당일 5분).
set -u
END=$(( $(date +%s) + 3300 ))
FORCE_FLAG="${FORCE_FLAG:-}"
while :; do
  python3 scripts/fetch_status.py $FORCE_FLAG || true
  python3 scripts/fetch_bus.py || true
  FORCE_FLAG=""; export FORCE=""      # 수동 강제 실행은 첫 회차만
  if [ -n "$(git status --porcelain status.json bus_status.json)" ]; then
    for f in status.json bus_status.json; do [ -e "$f" ] && git add "$f"; done
    git commit -q -m "항공편·버스 상태 갱신"
    for i in 1 2 3; do
      git pull --rebase -q origin main && git push -q origin HEAD:main && break
      sleep 4
    done
  fi
  NOW=$(date +%s)
  NEXT=$(( (NOW / 300 + 1) * 300 ))
  [ "$NEXT" -ge "$END" ] && break
  sleep $(( NEXT - NOW ))
done
