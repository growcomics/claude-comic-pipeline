#!/bin/bash
# beats with >=6 fresh variants, no winner banked, sheet built or not
cd "$(dirname "$0")"
for b in $(ls plan | sed 's/\.json$//'); do
  c=$(ls variants/$b 2>/dev/null | wc -l | tr -d ' ')
  w=$(python3 -c "import json;print((json.load(open('state.json'))['beats'].get('$b') or {}).get('winner') and 'W' or '-')")
  s=$([ -f "sheets/$b.jpg" ] && echo sheet || echo nosheet)
  echo "$b files=$c winner=$w $s"
done
