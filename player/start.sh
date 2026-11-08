#!/bin/sh
# SignageCast Player – Start: den vom Server aktualisierten Agenten (Boot-Partition) nehmen, solange er nicht
# dreimal hintereinander abstürzt; sonst den eingebauten aus dem Image.
# PC-Player (seit 0.36): statt der Boot-Partition die Datenpartition des USB-Sticks (medium.sh hängt sie ein).
B=/boot/firmware/signagecast/agent.py
if [ -e /etc/signagecast-pc ]; then
  /usr/lib/signagecast-player/medium.sh
  export SC_BOOT=/run/signagecast-medium
  B=$SC_BOOT/signagecast/agent.py
fi
Z=/run/signagecast/fehlstarts
mkdir -p /run/signagecast
n=$(cat "$Z" 2>/dev/null || echo 0)
if [ -f "$B" ] && [ "$n" -lt 3 ] && python3 -c 'import ast, sys; ast.parse(open(sys.argv[1]).read())' "$B" 2>/dev/null; then
  echo $((n + 1)) > "$Z"
  exec python3 -B "$B"
fi
exec python3 -B /usr/lib/signagecast-player/agent.py
