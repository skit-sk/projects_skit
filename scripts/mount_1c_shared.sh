#!/bin/bash
# mount_1c_shared.sh — подключение CIFS-шар 1c_shared в контейнер 0a71c9cc66d3
# Запуск (на хосте, от root):
#   /root/mount_1c_shared.sh
# Перед запуском заполнить PASSWORD ниже.
set -euo pipefail

CONTAINER="0a71c9cc66d3"
CIFS="//46.175.122.107/1c_shared"
USER_="oc_z_10_152"
DOMAIN="WORKGROUP"
PASSWORD=""   # ← ЗАПОЛНИТЬ: пароль от oc_z_10_152
OPTS_BASE="username=$USER_,domain=$DOMAIN,vers=3.0,cache=strict,soft,nounix,serverino,mapposix,iocharset=utf8,file_mode=0755,dir_mode=0755,uid=3002,forceuid,gid=3000,forcegid"

[ -n "$PASSWORD" ] || { echo "❌ Заполните PASSWORD в скрипте"; exit 1; }

PID=$(docker inspect -f '{{.State.Pid}}' "$CONTAINER")
[ -n "$PID" ] && [ "$PID" != "0" ] || { echo "❌ Контейнер $CONTAINER не найден"; exit 1; }
echo "Контейнер $CONTAINER, PID=$PID"

CREDS=$(mktemp /tmp/cifs-1c.XXXXXX); chmod 600 "$CREDS"
printf 'username=%s\ndomain=%s\npassword=%s\n' "$USER_" "$DOMAIN" "$PASSWORD" > "$CREDS"
trap 'rm -f "$CREDS"' EXIT

mount_in() {
  local share="$1" sub="$2" mode="$3" ro_opt=""
  [ "$mode" = "ro" ] && ro_opt="ro,"
  if nsenter -t "$PID" -m mount -t cifs "$CIFS/$share" "/shared/1c_shared/$sub" -o "${ro_opt}${OPTS_BASE},credentials=$CREDS" 2>/dev/null; then
    echo "✅ $sub ($mode): $CIFS/$share"
  else
    echo "❌ $sub: не удалось смонтировать (см. dmesg на хосте)"
  fi
}

mount_in "src"       "src"       ro
mount_in "history"   "history"   ro
mount_in "proposals" "proposals" rw

echo "--- Проверка в контейнере ---"
docker exec "$CONTAINER" ls /shared/1c_shared/src/ | head -10
docker exec "$CONTAINER" stat -c '%U %G' /shared/1c_shared/src
