#!/usr/bin/env bash
# set up hivebeat in a REAL termux shell (not inside proot).
# run this as the normal termux user:  bash setup_termux.sh
set -e
echo "== installing python + numpy + pulseaudio (termux) =="
pkg install -y python python-numpy pulseaudio
echo "== starting pulseaudio daemon =="
pulseaudio --start --exit-idle-time=-1 || true
sleep 2
echo "== loading the loopback TCP bridge (proot↔pulse needs it) =="
pactl load-module module-native-protocol-tcp auth-anonymous=1 listen=127.0.0.1 port=4713 >/dev/null 2>&1 || true
echo "== done. launch the hive with: =="
echo "    ./hivebeat"
echo " (or ./play.sh out.wav 8 \"p1 >> saw(\\\"c4 e4 g4\\\", dur=0.5)\" \"kick >> beat(euclid(3,8), dur=0.25)\")"
