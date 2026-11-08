#!/usr/bin/env python3
"""Genera la programación (EPG) de CaféTV.
1) Elige los canales de "Mi lista" que tienen guía en iptv-org.
2) Crea custom.channels.xml para el grabber de iptv-org/epg.
3) Con --convert, pasa guide.xml a epg/epg.json (formato compacto para la app).
"""
import json, re, sys, time, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime

API = 'https://iptv-org.github.io/api/'
HIS = 'CO MX AR CL PE VE EC BO PY UY CR PA DO GT HN SV NI CU PR ES'.split()
NOCAT = {'religious', 'shop', 'legislative', 'xxx'}
PAGO = re.compile(r'(espn|dsports|directv|bein|fox sports|fox deportes|win sports|win\+|tnt|hbo|cinemax|star channel|star\+|disney|golf channel|eurosport|msg|tyc sports|l1 max|bicolor|universal|warner|axn|sony|amc|cinecanal|paramount|discovery|nat ?geo|national geographic|history|a&e|lifetime|cartoon|nickelodeon|nick jr|comedy central|mtv|tlc|animal planet|golden|de pel[ií]cula|tooncast|cartoonito|baby ?tv|tudn|gol ?tv|movistar|dazn|sky sports|fubo|cinelatino|claro cinema|film ?& ?arts|europa europa|^dhe$|^ifc$|az cinema|az corazon|az clic|studio)', re.I)
REGIONAL = re.compile(r'(canarias|catalu|m[aá]laga|andaluc|galicia|valencia|murcia|euskadi|asturias|arag[oó]n|baleares|extremadura|navarra|rioja|castilla|cantabria|sevilla|granada|alicante|tenerife)', re.I)
SITE_PREF = ['pluto.tv', 'mi.tv', 'gatotv.com', 'siba.com.co', 'tvguia.es', 'movistarplus.es']
SITE_SKIP = {'i.mjh.nz'}

def get(name):
    with urllib.request.urlopen(API + name + '.json', timeout=120) as r:
        return json.load(r)

def make_channels(out_path):
    channels = get('channels'); feeds = get('feeds'); streams = get('streams'); guides = get('guides')
    lang = {}
    for f in feeds:
        for l in f.get('languages') or []:
            lang.setdefault(f['channel'], set()).add(l)
    has_stream = {s['channel'] for s in streams if s.get('channel')}
    wanted = {}
    for c in channels:
        cid = c['id']
        if cid not in has_stream or c.get('closed') or c.get('is_nsfw'):
            continue
        cats = set(c.get('categories') or [])
        if cats & NOCAT or PAGO.search(c['name']):
            continue
        spa = ('spa' in lang[cid]) if cid in lang else c.get('country') in HIS
        eng_movie = 'movies' in cats and 'eng' in lang.get(cid, set())
        if not (spa or eng_movie):
            continue
        if spa and c.get('country') != 'CO' and REGIONAL.search(c['name']):
            continue
        wanted[cid] = c['name']
    best = {}
    for g in guides:
        cid = g.get('channel')
        if cid not in wanted or g['site'] in SITE_SKIP:
            continue
        rank = SITE_PREF.index(g['site']) if g['site'] in SITE_PREF else 50
        if g.get('lang') == 'es':
            rank -= 0.5
        if cid not in best or rank < best[cid][0]:
            best[cid] = (rank, g)
    root = ET.Element('channels')
    for cid, (_, g) in sorted(best.items()):
        e = ET.SubElement(root, 'channel', site=g['site'], lang=g.get('lang') or 'es',
                          xmltv_id=cid, site_id=g['site_id'])
        e.text = g.get('site_name') or wanted[cid]
    ET.ElementTree(root).write(out_path, encoding='utf-8', xml_declaration=True)
    print(f'{len(best)} canales con guía de {len(wanted)} elegidos')

def ts(s):
    # formato XMLTV: 20261108183000 +0000
    return int(datetime.strptime(s.strip(), '%Y%m%d%H%M%S %z').timestamp() // 60)

def convert(guide_path, out_path):
    now = int(time.time() // 60)
    lo, hi = now - 180, now + 36 * 60
    data = {}
    for _, el in ET.iterparse(guide_path, events=('end',)):
        if el.tag != 'programme':
            continue
        try:
            a, b = ts(el.get('start')), ts(el.get('stop'))
        except Exception:
            el.clear(); continue
        if b < lo or a > hi:
            el.clear(); continue
        cid = (el.get('channel') or '').split('@')[0]
        t = el.findtext('title') or ''
        data.setdefault(cid, []).append([a, b, t.strip()[:80]])
        el.clear()
    for cid in data:
        data[cid].sort()
        data[cid] = data[cid][:60]
    out = {'generated': now, 'channels': data}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{len(data)} canales con programación guardados en {out_path}')

if __name__ == '__main__':
    if sys.argv[1] == '--channels':
        make_channels(sys.argv[2])
    elif sys.argv[1] == '--convert':
        convert(sys.argv[2], sys.argv[3])
