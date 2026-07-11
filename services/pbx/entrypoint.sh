#!/bin/sh
set -eu

EXT_1001_PASSWORD="${FREESWITCH_EXTENSION_1001_PASSWORD:-1001pass}"
EXT_1002_PASSWORD="${FREESWITCH_EXTENSION_1002_PASSWORD:-1002pass}"
EVENT_SOCKET_PASSWORD="${FREESWITCH_EVENT_SOCKET_PASSWORD:-ClueCon}"

if [ ! -f "/etc/freeswitch/freeswitch.xml" ]; then
  mkdir -p /etc/freeswitch
  cp -varf /usr/share/freeswitch/conf/vanilla/* /etc/freeswitch/
fi

mkdir -p /etc/freeswitch/directory/default /etc/freeswitch/dialplan/default
cp /voxagent-freeswitch/directory/default/1001.xml /etc/freeswitch/directory/default/1001.xml
cp /voxagent-freeswitch/directory/default/1002.xml /etc/freeswitch/directory/default/1002.xml
cp /voxagent-freeswitch/dialplan/default/10_extensions.xml /etc/freeswitch/dialplan/default/10_extensions.xml
cp /voxagent-freeswitch/dialplan/default/20_placeholders.xml /etc/freeswitch/dialplan/default/20_placeholders.xml

sed -i "s|__EXT_1001_PASSWORD__|${EXT_1001_PASSWORD}|g" /etc/freeswitch/directory/default/1001.xml
sed -i "s|__EXT_1002_PASSWORD__|${EXT_1002_PASSWORD}|g" /etc/freeswitch/directory/default/1002.xml
sed -i "s|<param name=\"listen-ip\" value=\"::\"/>|<param name=\"listen-ip\" value=\"127.0.0.1\"/>|g" /etc/freeswitch/autoload_configs/event_socket.conf.xml
sed -i "s|<param name=\"password\" value=\"ClueCon\"/>|<param name=\"password\" value=\"${EVENT_SOCKET_PASSWORD}\"/>|g" /etc/freeswitch/autoload_configs/event_socket.conf.xml

trap '/usr/bin/freeswitch -stop' TERM

/usr/bin/freeswitch -nc -nf -nonat &
pid="$!"

wait "$pid"
