"""Posts the day's planned Focusland post to Instagram @focusland.app.

Runs in a Claude cloud routine. The Instagram token is never in this file or the repo:
the cloud environment's network proxy adds it to every request to graph.instagram.com.

Usage:
  python3 social/post.py --slot am      post today's 8 AM (Manila) item, if any
  python3 social/post.py --slot pm      post today's 8 PM (Manila) item, if any
  python3 social/post.py --check        only check that the Instagram connection works

It marks the item "posted" in social/queue.json; commit and push that change afterwards.
Exit code 0 = posted or nothing to post, 1 = something went wrong (nothing marked).
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = 'https://graph.instagram.com'
HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, 'queue.json')
MANILA = datetime.timezone(datetime.timedelta(hours=8))


def call(method, path, params=None):
    data = urllib.parse.urlencode(params or {}).encode() if method == 'POST' else None
    url = API + path + ('' if method == 'POST' or not params else '?' + urllib.parse.urlencode(params))
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{method} {path} failed: {e.code} {e.read().decode()[:400]}')


def wait_ready(container_id, minutes=8):
    # Videos (Reels) need processing before they can be published
    deadline = time.time() + minutes * 60
    while time.time() < deadline:
        status = call('GET', f'/{container_id}', {'fields': 'status_code,status'})
        code = status.get('status_code')
        if code == 'FINISHED':
            return
        if code in ('ERROR', 'EXPIRED'):
            raise RuntimeError(f'media processing failed: {status}')
        time.sleep(10)
    raise RuntimeError('media took too long to process')


def publish(item, base):
    url = lambda f: base + f
    kind = item['kind']
    if kind == 'image':
        c = call('POST', '/me/media', {'image_url': url(item['files'][0]), 'caption': item['caption']})
    elif kind == 'carousel':
        children = []
        for f in item['files']:
            ch = call('POST', '/me/media', {'image_url': url(f), 'is_carousel_item': 'true'})
            children.append(ch['id'])
        for ch in children:
            wait_ready(ch, minutes=3)
        c = call('POST', '/me/media', {'media_type': 'CAROUSEL', 'children': ','.join(children), 'caption': item['caption']})
    elif kind == 'reel':
        params = {'media_type': 'REELS', 'video_url': url(item['files'][0]), 'caption': item['caption'], 'share_to_feed': 'true'}
        if item.get('cover'):
            params['cover_url'] = url(item['cover'])
        c = call('POST', '/me/media', params)
    else:
        raise RuntimeError(f'unknown kind {kind}')
    wait_ready(c['id'])
    done = call('POST', '/me/media_publish', {'creation_id': c['id']})
    return done['id']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slot', choices=['am', 'pm'])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--date', help='override today (YYYY-MM-DD, Manila)')
    a = ap.parse_args()

    if a.check:
        me = call('GET', '/me', {'fields': 'username,account_type'})
        print(f'connected as @{me.get("username")} ({me.get("account_type")})')
        return 0

    q = json.load(open(QUEUE, encoding='utf-8'))
    today = a.date or datetime.datetime.now(MANILA).date().isoformat()
    todo = [i for i in q['items'] if i['date'] == today and i['slot'] == a.slot and not i['posted']]
    if not todo:
        later = [i for i in q['items'] if not i['posted']]
        print(f'nothing planned for {today} {a.slot}. {len(later)} posts left in the queue.')
        return 0
    item = todo[0]
    me = call('GET', '/me', {'fields': 'username'})
    if me.get('username') != q['account']:
        print(f'refusing to post: token belongs to @{me.get("username")}, expected @{q["account"]}')
        return 1
    media_id = publish(item, q['media_base'])
    item['posted'] = True
    item['posted_at'] = datetime.datetime.now(MANILA).isoformat(timespec='minutes')
    item['media_id'] = media_id
    json.dump(q, open(QUEUE, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    left = len([i for i in q['items'] if not i['posted']])
    print(f'posted {item["kind"]} {item["files"][0]} for {today} {a.slot} (media {media_id}). {left} posts left.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f'error: {e}')
        sys.exit(1)
