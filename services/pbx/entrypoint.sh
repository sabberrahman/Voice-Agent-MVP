#!/bin/sh
set -eu

EXT_1001_PASSWORD="${FREESWITCH_EXTENSION_1001_PASSWORD:-1001pass}"
EXT_1002_PASSWORD="${FREESWITCH_EXTENSION_1002_PASSWORD:-1002pass}"
EVENT_SOCKET_PASSWORD="${FREESWITCH_EVENT_SOCKET_PASSWORD:-ClueCon}"
FREESWITCH_DOMAIN="${FREESWITCH_DOMAIN:-${ZOIPER_HOST_IP:-}}"
FREESWITCH_RTP_START="${FREESWITCH_RTP_START:-16384}"
FREESWITCH_RTP_END="${FREESWITCH_RTP_END:-16484}"

if [ -d "/usr/local/freeswitch/etc/freeswitch" ]; then
  FS_CONF_DIR="/usr/local/freeswitch/etc/freeswitch"
elif [ -d "/usr/local/freeswitch/conf" ]; then
  FS_CONF_DIR="/usr/local/freeswitch/conf"
else
  FS_CONF_DIR="/etc/freeswitch"
fi
EVENT_SOCKET_CONF="${FS_CONF_DIR}/autoload_configs/event_socket.conf.xml"
MODULES_CONF="${FS_CONF_DIR}/autoload_configs/modules.conf.xml"
SWITCH_CONF="${FS_CONF_DIR}/autoload_configs/switch.conf.xml"
INTERNAL_SIP_PROFILE="${FS_CONF_DIR}/sip_profiles/internal.xml"

if [ ! -f "${FS_CONF_DIR}/freeswitch.xml" ]; then
  mkdir -p "${FS_CONF_DIR}"
  if [ -d "/usr/share/freeswitch/conf/vanilla" ]; then
    cp -varf /usr/share/freeswitch/conf/vanilla/* "${FS_CONF_DIR}/"
  fi
fi

mkdir -p "${FS_CONF_DIR}/directory/default" "${FS_CONF_DIR}/dialplan/default"
cp /voxagent-freeswitch/directory/default/1001.xml "${FS_CONF_DIR}/directory/default/1001.xml"
cp /voxagent-freeswitch/directory/default/1002.xml "${FS_CONF_DIR}/directory/default/1002.xml"
cp /voxagent-freeswitch/dialplan/default/10_extensions.xml "${FS_CONF_DIR}/dialplan/default/10_extensions.xml"
cp /voxagent-freeswitch/dialplan/default/20_placeholders.xml "${FS_CONF_DIR}/dialplan/default/20_placeholders.xml"

sed -i "s|__EXT_1001_PASSWORD__|${EXT_1001_PASSWORD}|g" "${FS_CONF_DIR}/directory/default/1001.xml"
sed -i "s|__EXT_1002_PASSWORD__|${EXT_1002_PASSWORD}|g" "${FS_CONF_DIR}/directory/default/1002.xml"
sed -i "s|<param name=\"listen-ip\" value=\"::\"/>|<param name=\"listen-ip\" value=\"0.0.0.0\"/>|g" "${EVENT_SOCKET_CONF}"
sed -i "s|<param name=\"listen-ip\" value=\"127.0.0.1\"/>|<param name=\"listen-ip\" value=\"0.0.0.0\"/>|g" "${EVENT_SOCKET_CONF}"
sed -i "s|<param name=\"password\" value=\"[^\"]*\"/>|<param name=\"password\" value=\"${EVENT_SOCKET_PASSWORD}\"/>|g" "${EVENT_SOCKET_CONF}"

if [ -f "${SWITCH_CONF}" ]; then
  sed -i "/<param name=\"rtp-start-port\"/d" "${SWITCH_CONF}"
  sed -i "/<param name=\"rtp-end-port\"/d" "${SWITCH_CONF}"
  sed -i "/<settings>/a\\    <param name=\"rtp-start-port\" value=\"${FREESWITCH_RTP_START}\"/>\\
    <param name=\"rtp-end-port\" value=\"${FREESWITCH_RTP_END}\"/>" "${SWITCH_CONF}"
fi

if [ -n "${FREESWITCH_DOMAIN}" ] && [ -f "${INTERNAL_SIP_PROFILE}" ]; then
  for param in sip-ip rtp-ip ext-sip-ip ext-rtp-ip; do
    sed -i "/<param name=\"${param}\"/d" "${INTERNAL_SIP_PROFILE}"
  done
  sed -i "/<settings>/a\\    <param name=\"sip-ip\" value=\"0.0.0.0\"/>\\
    <param name=\"rtp-ip\" value=\"0.0.0.0\"/>\\
    <param name=\"ext-sip-ip\" value=\"${FREESWITCH_DOMAIN}\"/>\\
    <param name=\"ext-rtp-ip\" value=\"${FREESWITCH_DOMAIN}\"/>" "${INTERNAL_SIP_PROFILE}"
fi

if ! grep -Eq '^[[:space:]]*<load module="mod_event_socket"/>' "${MODULES_CONF}"; then
  sed -i 's|</modules>|  <load module="mod_event_socket"/>\
</modules>|' "${MODULES_CONF}"
fi

if ! grep -Eq '^[[:space:]]*<load module="mod_audio_stream"/>' "${MODULES_CONF}"; then
  sed -i 's|</modules>|  <load module="mod_audio_stream"/>\
</modules>|' "${MODULES_CONF}"
fi

trap '/usr/bin/freeswitch -stop' TERM

/usr/bin/freeswitch -nc -nf -nonat &
pid="$!"

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if fs_cli -x status >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! fs_cli -x 'sofia status' >/dev/null 2>&1; then
  fs_cli -x 'load mod_sofia' >/dev/null 2>&1 || true
fi

fs_cli -x 'sofia profile internal rescan' >/dev/null 2>&1 || true

wait "$pid"
