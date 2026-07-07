#!/usr/bin/env python3
"""monday-import.py — one-time Monday.com "Operations" board xlsx -> studio ops board JSON.

Reads the raw xlsx (zipfile + ElementTree, stdlib only — the exported workbook uses
inline strings; shared strings are handled too just in case) and emits:

  data/ops-tasks.json    {meta, tasks:[...]}          (schema: see inc/ops.php)
  data/ops-updates.json  {taskId: [update, ...]}      (Monday update threads, read-only)
  data/import-report.txt human-readable audit of everything mapped / skipped / unknown

The operations sheet is a Monday export: group header rows ("To do" / "done" /
"Cancelled" / "On hold") partition the tasks; a few tasks carry an embedded
sub-board ("Subitems | Name | Owner | Status | ..." header followed by rows with an
empty first cell) whose rows become the parent task's checklist. Site + person cells
are comma-separated; sites normalize against cc-sites.json aliases.

Usage:  python3 monday-import.py <export.xlsx> [--data-dir ../data]
"""
import argparse
import datetime as dt
import json
import re
import secrets
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

GROUP_MAP = {'to do': 'todo', 'done': 'done', 'cancelled': 'cancelled', 'on hold': 'onhold'}
STATUS_MAP = {
    '': 'notstarted', 'not started': 'notstarted', 'working on it': 'working',
    'done': 'done', 'on-hold': 'onhold', 'on hold': 'onhold',
    'cancelled': 'cancelled', 'confirmation needed': 'confirm',
}
PRIORITY_MAP = {'': '', 'low': 'low', 'medium': 'medium', 'high': 'high', 'critical': 'critical'}
PERSON_MAP = {'grow comics': 'GrowGetter'}   # same owner, second Monday account


# ---- xlsx plumbing ----------------------------------------------------------

def col_letter(ref: str) -> str:
    return re.match(r'([A-Z]+)', ref).group(1) if ref and re.match(r'[A-Z]+', ref) else ''


def col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def load_shared_strings(z: zipfile.ZipFile):
    try:
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
    except KeyError:
        return []
    return [''.join(t.text or '' for t in si.findall('.//m:t', NS)) for si in root.findall('m:si', NS)]


def sheet_rows(z: zipfile.ZipFile, path: str, shared):
    """Yield each row as a list of cell strings, positioned by the cell's r= column ref."""
    root = ET.fromstring(z.read(path))
    for row in root.findall('.//m:row', NS):
        cells = {}
        fallback_col = 0
        for c in row.findall('m:c', NS):
            ref = c.get('r') or ''
            idx = col_index(col_letter(ref)) if col_letter(ref) else fallback_col
            fallback_col = idx + 1
            t = c.get('t')
            if t == 'inlineStr':
                v = ''.join(x.text or '' for x in c.findall('.//m:t', NS))
            else:
                el = c.find('m:v', NS)
                v = el.text if el is not None and el.text is not None else ''
                if t == 's' and v != '':
                    v = shared[int(v)]
            cells[idx] = v
        width = max(cells) + 1 if cells else 0
        yield [cells.get(i, '') for i in range(width)]


def sheet_paths(z: zipfile.ZipFile):
    """Map sheet name -> xl/worksheets/sheetN.xml via workbook rels."""
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rel_ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
    rid_target = {rel.get('Id'): rel.get('Target') for rel in rels.findall('r:Relationship', rel_ns)}
    out = {}
    for s in wb.findall('.//m:sheet', NS):
        rid = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = rid_target.get(rid, '')
        out[s.get('name')] = 'xl/' + target.lstrip('/') if not target.startswith('xl/') else target
    return out


# ---- field parsing ----------------------------------------------------------

CREATION_RE = re.compile(r'^(.*?)\s+([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M)$')


def parse_creation_log(raw: str, report):
    raw = raw.strip()
    if raw == '':
        return '', ''
    m = CREATION_RE.match(raw)
    if not m:
        report['unparsed_dates'].append(f'creation log: {raw!r}')
        return raw, ''
    who = m.group(1).strip()
    try:
        d = dt.datetime.strptime(m.group(2), '%b %d, %Y %I:%M %p')
        return who, d.strftime('%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        report['unparsed_dates'].append(f'creation log: {raw!r}')
        return who, ''


def parse_completed_on(raw: str, report):
    raw = raw.strip()
    if raw == '':
        return ''
    if re.fullmatch(r'\d{4,6}(\.\d+)?', raw):        # Excel serial date
        d = dt.datetime(1899, 12, 30) + dt.timedelta(days=float(raw))
        return d.strftime('%Y-%m-%dT%H:%M:%SZ')
    report['unparsed_dates'].append(f'completed on kept verbatim: {raw!r}')
    return raw


def parse_update_ts(raw: str, report):
    raw = re.sub(r'\s+', ' ', raw.strip())
    if raw == '':
        return ''
    try:
        d = dt.datetime.strptime(raw, '%d/%B/%Y %I:%M:%S %p')
        return d.strftime('%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        report['unparsed_dates'].append(f'update ts kept verbatim: {raw!r}')
        return raw


def split_csv(raw: str):
    return [p.strip() for p in raw.split(',') if p.strip()]


# ---- main -------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('xlsx')
    ap.add_argument('--data-dir', default=str(Path(__file__).resolve().parent.parent / 'data'))
    args = ap.parse_args()
    data_dir = Path(args.data_dir)

    sites_reg = json.loads((data_dir / 'cc-sites.json').read_text())
    alias_map = {}
    for key, site in sites_reg.items():
        alias_map[key.lower()] = key
        alias_map[site['name'].lower()] = key
        for a in site.get('aliases', []):
            alias_map[a.lower()] = key

    report = {'groups': {}, 'statuses': {}, 'unknown_sites': [], 'unparsed_dates': [],
              'skipped_rows': [], 'orphan_updates': [], 'unmapped_status': [], 'unmapped_priority': []}

    z = zipfile.ZipFile(args.xlsx)
    shared = load_shared_strings(z)
    paths = sheet_paths(z)
    ops_path = paths.get('operations') or 'xl/worksheets/sheet1.xml'
    upd_path = paths.get('updates') or 'xl/worksheets/sheet2.xml'

    now_iso = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # ---- operations sheet ----
    tasks = []
    ids_used = set()
    group = 'todo'
    in_subitems = False
    sort_counters = {}

    def new_id():
        while True:
            i = secrets.token_hex(5)
            if i not in ids_used:
                ids_used.add(i)
                return i

    for rownum, row in enumerate(sheet_rows(z, ops_path, shared)):
        cells = [c.strip() if isinstance(c, str) else c for c in row]
        pad = cells + [''] * (10 - len(cells))
        a = pad[0]

        low = a.lower()
        if low in GROUP_MAP and pad[3] == '' and pad[9] == '':          # group divider row
            group = GROUP_MAP[low]
            in_subitems = False
            continue
        if a == 'Name' and pad[1] == 'Subitems':                        # main header row
            in_subitems = False
            continue
        if a == 'Subitems' and pad[1] == 'Name':                        # embedded sub-board header
            in_subitems = True
            continue
        if in_subitems and a == '' and pad[1] != '':                    # subitem row -> checklist on last task
            if tasks:
                tasks[-1]['checklist'].append({
                    'text': pad[1],
                    'done': pad[3].strip().lower() == 'done',
                    'mondayId': pad[6] if len(cells) > 6 else '',
                })
            continue
        in_subitems = False

        monday_id = pad[9].strip()
        if a == '' and monday_id == '':                                 # blank / decoration row
            if any(pad):
                report['skipped_rows'].append(f'row {rownum}: {" | ".join(x for x in pad if x)[:120]}')
            continue
        if monday_id == '':                                             # named but no Item ID
            report['skipped_rows'].append(f'row {rownum} (no Item ID): {a[:120]}')
            continue

        raw_status = pad[3].strip()
        status = STATUS_MAP.get(raw_status.lower())
        if status is None:
            report['unmapped_status'].append(f'{raw_status!r} on {a[:60]!r}')
            status = 'notstarted'
        raw_pri = pad[6].strip().replace('⚠️️', '').replace('⚠️', '').strip()
        priority = PRIORITY_MAP.get(raw_pri.lower())
        if priority is None:
            report['unmapped_priority'].append(f'{pad[6]!r} on {a[:60]!r}')
            priority = ''

        persons, seen_p = [], set()
        for p in split_csv(pad[2]):
            p = PERSON_MAP.get(p.lower(), p)
            if p.lower() not in seen_p:
                seen_p.add(p.lower())
                persons.append(p)

        sites, sites_raw = [], []
        for s in split_csv(pad[5]):
            k = alias_map.get(s.lower())
            if k:
                if k not in sites:
                    sites.append(k)
            else:
                sites_raw.append(s)
                report['unknown_sites'].append(f'{s!r} on {a[:60]!r}')

        created_by, created = parse_creation_log(pad[8], report)
        rev = pad[4].strip()

        task = {
            'id': new_id(),
            'mondayId': monday_id,
            'title': a,
            'body': '',
            'checklist': [],
            'group': group,
            'status': status,
            'mondayStatus': raw_status,
            'person': persons,
            'sites': sites,
            'priority': priority,
            'revenueImpact': int(float(rev)) if re.fullmatch(r'\d+(\.\d+)?', rev) else 0,
            'aiTag': '', 'aiPlan': '', 'batch': '',
            'createdBy': created_by,
            'created': created or now_iso,
            'updated': now_iso,
            'completedOn': parse_completed_on(pad[7], report),
            'creationLog': pad[8].strip(),
            'archived': False,
            'sort': sort_counters.setdefault(group, 0),
        }
        if sites_raw:
            task['sitesRaw'] = sites_raw
        sort_counters[group] += 1
        tasks.append(task)
        report['groups'][group] = report['groups'].get(group, 0) + 1
        report['statuses'][status] = report['statuses'].get(status, 0) + 1

    by_monday = {t['mondayId']: t['id'] for t in tasks}
    for t in tasks:                                   # subitem updates land on the parent task
        for c in t['checklist']:
            if c.get('mondayId') and c['mondayId'] not in by_monday:
                by_monday[c['mondayId']] = t['id']

    # ---- updates sheet ----
    updates = {}
    n_updates = 0
    for rownum, row in enumerate(sheet_rows(z, upd_path, shared)):
        pad = list(row) + [''] * (11 - len(row))
        item_id = str(pad[0]).strip()
        if rownum < 2 or item_id == '' or item_id == 'Item ID':
            continue
        task_id = by_monday.get(item_id)
        if not task_id:
            report['orphan_updates'].append(f'item {item_id} ({str(pad[1])[:60]!r})')
            continue
        text = str(pad[6]).replace('\r\n', '\n').strip()
        entry = {
            'id': str(pad[9]).strip() or secrets.token_hex(5),
            'parent': str(pad[10]).strip(),
            'src': 'monday',
            'by': str(pad[4]).strip(),
            'ts': parse_update_ts(str(pad[5]), report),
            'text': text,
            'likes': int(pad[7]) if str(pad[7]).strip().isdigit() else 0,
            'assets': split_csv(str(pad[8])),
        }
        updates.setdefault(task_id, []).append(entry)
        n_updates += 1
    for tid in updates:
        updates[tid].sort(key=lambda u: u['ts'])

    # ---- write ----
    out_tasks = {
        'meta': {'importedAt': now_iso, 'source': 'monday-operations-export', 'importedCount': len(tasks)},
        'tasks': tasks,
    }
    (data_dir / 'ops-tasks.json').write_text(json.dumps(out_tasks, indent=1, ensure_ascii=False) + '\n')
    (data_dir / 'ops-updates.json').write_text(json.dumps(updates, indent=1, ensure_ascii=False) + '\n')

    lines = [f'Monday import — {now_iso}', f'source: {args.xlsx}', '',
             f'tasks imported: {len(tasks)}',
             f'  by group:  {json.dumps(report["groups"])}',
             f'  by status: {json.dumps(report["statuses"])}',
             f'  with checklist: {sum(1 for t in tasks if t["checklist"])} '
             f'({sum(len(t["checklist"]) for t in tasks)} items)',
             f'updates imported: {n_updates} across {len(updates)} tasks', '']
    for key in ('unmapped_status', 'unmapped_priority', 'unknown_sites', 'unparsed_dates', 'skipped_rows', 'orphan_updates'):
        vals = report[key]
        lines.append(f'{key}: {len(vals)}')
        lines.extend(f'  - {v}' for v in vals)
    (data_dir / 'import-report.txt').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    sys.exit(main())
