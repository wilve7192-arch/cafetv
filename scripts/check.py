#!/usr/bin/env python3
"""Comprueba las señales de los canales de CaféTV y guarda las que funcionan
en status/status.json. Solo usa la biblioteca estándar de Python."""
import json, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, 'scripts')
from epg import get, HIS, NOCAT, PAGO, REGIONAL  # mismas reglas de selección

UA = 'Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0 TV Safari/537.36'

def fetch(url, ua=None, ref=None, limit=200000):
    h = {'User-Agent': ua or UA}
    if ref:
        h['Referer'] = ref
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.geturl(), r.read(limit)

def check(stream):
    url, ua, ref = stream['url'], stream.get('user_agent'), stream.get('referrer')
    try:
        base, body = fetch(url, ua, ref)
        text = body.decode('utf-8', 'ignore')
        if '#EXTM3U' not in text:
            return False
        for _ in range(2):  # lista maestra -> variante -> segmento
            lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith('#')]
            if not lines:
                return False
            nxt = urllib.parse.urljoin(base, lines[0])
            if '.m3u8' in nxt.split('?')[0] or 'EXT-X-STREAM-INF' in text:
                base, body = fetch(nxt, ua, ref)
                text = body.decode('utf-8', 'ignore')
                continue
            fetch(nxt, ua, ref, limit=4096)  # el primer segmento responde
            return True
        return False
    except Exception:
        return False

def main(out):
    channels = get('channels'); feeds = get('feeds'); streams = get('streams')
    lang = {}
    for f in feeds:
        for l in f.get('languages') or []:
            lang.setdefault(f['channel'], set()).add(l)
    wanted = set()
    for c in channels:
        cats = set(c.get('categories') or [])
        if c.get('closed') or c.get('is_nsfw') or cats & NOCAT or PAGO.search(c['name']):
            continue
        cid = c['id']
        spa = ('spa' in lang[cid]) if cid in lang else c.get('country') in HIS
        eng_movie = 'movies' in cats and 'eng' in lang.get(cid, set())
        if spa and c.get('country') != 'CO' and REGIONAL.search(c['name']):
            continue
        if spa or eng_movie:
            wanted.add(cid)
    todo = [s for s in streams if s.get('channel') in wanted and s.get('url')]
    print(f'Comprobando {len(todo)} señales de {len(wanted)} canales…', flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(64) as ex:
        res = list(ex.map(check, todo))
    ok = sorted({s['url'] for s, r in zip(todo, res) if r})
    alive = {s['channel'] for s, r in zip(todo, res) if r}
    data = {'generated': int(time.time() // 60), 'checked': len(todo), 'channels': len(wanted),
            'alive_channels': len(alive), 'ok': ok}
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f'Listo en {int(time.time()-t0)} s: {len(ok)}/{len(todo)} señales y {len(alive)}/{len(wanted)} canales funcionan')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'status/status.json')
