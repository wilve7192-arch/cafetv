#!/usr/bin/env python3
"""Crea data/api.json: una versión reducida de la API de iptv-org (solo lo que usa CaféTV).
Pasa de ~26 MB a menos de 1 MB para que la app abra rápido en el TV."""
import json, sys, time, urllib.request

API = 'https://iptv-org.github.io/api/'
HIS = set('CO MX AR CL PE VE EC BO PY UY CR PA DO GT HN SV NI CU PR ES'.split())

def get(name):
    with urllib.request.urlopen(API + name + '.json', timeout=120) as r:
        return json.load(r)

def main(out):
    channels, streams, logos, feeds = get('channels'), get('streams'), get('logos'), get('feeds')
    countries, categories = get('countries'), get('categories')
    lang = {}
    for f in feeds:
        for l in f.get('languages') or []:
            lang.setdefault(f['channel'], set()).add(l)
    with_stream = {s['channel'] for s in streams if s.get('channel')}
    keep = {}
    for c in channels:
        cid = c['id']
        if cid not in with_stream or c.get('closed') or c.get('is_nsfw'):
            continue
        langs = lang.get(cid)
        spa = ('spa' in langs) if langs else c.get('country') in HIS
        if spa or c.get('country') == 'CO':
            keep[cid] = {'id': cid, 'name': c['name'], 'country': c.get('country'),
                         'categories': c.get('categories') or []}
    st = [{k: s[k] for k in ('channel', 'title', 'url', 'quality', 'referrer', 'user_agent') if s.get(k)}
          for s in streams if s.get('channel') in keep and s.get('url')]
    lg = {}
    for l in logos:
        if l['channel'] in keep and (l['channel'] not in lg or not l.get('feed')):
            lg[l['channel']] = {'channel': l['channel'], 'url': l['url']}
    fe = [{'channel': cid, 'languages': sorted(lang[cid])} for cid in keep if cid in lang]
    data = {'generated': int(time.time() // 60), 'channels': list(keep.values()), 'streams': st,
            'logos': list(lg.values()), 'feeds': fe,
            'countries': [{'code': c['code'], 'name': c['name'], 'flag': c.get('flag', '')} for c in countries],
            'categories': [{'id': c['id'], 'name': c['name']} for c in categories]}
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{len(keep)} canales, {len(st)} señales')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'data/api.json')
