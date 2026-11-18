#!/usr/bin/env python3
"""Descarga guías XMLTV públicas y genera epg/epg.json para CaféTV.
Solo descarga datos (no ejecuta programas de terceros). Biblioteca estándar de Python."""
import gzip, io, json, re, sys, time, unicodedata, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

PAISES = ['co', 'mx', 'ar', 'cl', 'pe', 've', 'ec', 'es']
FUENTES = [f'https://iptv-epg.org/files/epg-{p}.xml' for p in PAISES] + \
          [f'https://iptv-epg.org/files/epg-{p}.xml.gz' for p in PAISES]
UA = 'Mozilla/5.0 (CafeTV EPG)'

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', s)

def ts(s):
    return int(datetime.strptime(s.strip()[:20], '%Y%m%d%H%M%S %z').timestamp() // 60)

def bajar(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    return data

def main(out):
    now = int(time.time() // 60)
    lo, hi = now - 60, now + 14 * 60
    progs, nombres, ok = {}, {}, []
    for url in FUENTES:
        try:
            data = bajar(url)
        except Exception as e:
            print('✗', url, e)
            continue
        if b'<tv' not in data[:2000]:
            print('✗', url, 'no es XMLTV'); continue
        ok.append(url); n = 0
        for _, el in ET.iterparse(io.BytesIO(data), events=('end',)):
            if el.tag == 'channel':
                cid = el.get('id') or ''
                for dn in el.findall('display-name'):
                    if dn.text:
                        txt = re.sub(r'^[A-Z]{2}\s*-\s*', '', dn.text.strip())  # quita "CO - "
                        nombres.setdefault(cid, set()).add(norm(txt))
                nombres.setdefault(cid, set()).add(norm(cid.split('@')[0].split('.')[0]))
                el.clear()
            elif el.tag == 'programme':
                try:
                    a, b = ts(el.get('start')), ts(el.get('stop'))
                except Exception:
                    el.clear(); continue
                titulo = (el.findtext('title') or '').strip()
                if b >= lo and a <= hi and titulo and titulo.lower() not in ('no data', 'sin datos', 'no information', 'to be announced'):
                    progs.setdefault(el.get('channel') or '', []).append([a, b, titulo[:70]])
                    n += 1
                el.clear()
        print('✓', url, n, 'programas')
    salida, alias = {}, {}
    for cid, lista in progs.items():
        lista.sort(); vistos = set(); limpia = []
        for p in lista:
            if p[0] in vistos: continue
            vistos.add(p[0]); limpia.append(p)
        if len({p[2] for p in limpia}) < 2 and len(limpia) > 3:
            continue  # relleno sin programación real
        key = cid.split('@')[0]
        salida[key] = limpia[:20]
        for nm in nombres.get(cid, ()):
            if nm and nm not in alias:
                alias[nm] = key
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'generated': now, 'sources': ok, 'channels': salida, 'alias': alias}, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{len(progs)} canales con programación desde {len(ok)} fuentes')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'epg/epg.json')
