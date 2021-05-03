#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import urllib3
import argparse
from urllib.parse import urlencode

iz_url = 'https://countee-impfee.b-cdn.net/api/1.1/de/counters/getAll/_iz_sachsen?cached=impfee'
cool_down_time = 60 * 10
sleep_interval = 60 *  1

bot_url = 'https://api.telegram.org/bot{auth}/sendMessage?chat_id={id}&{msg}'

if 'https_proxy' in os.environ:
    http = urllib3.ProxyManager(os.environ['https_proxy'])
else:
    http = urllib3.PoolManager()

def send_telegram_message(auth, id, msg):
    uri = bot_url.format(auth = auth, id = id, msg = urlencode({'text' : msg}))
    request = http.request('GET', uri)

def p_or_ps(count):
    return ' freier Platz' if (1 == count) else ' freie Plätze'

def in_limits(name, count):
    ret = ''
    for key in limits.keys():
        limit = limits[key]['limit']
        if key in name and ((limit > 0 and count >= limit) or (limit == 0 and count > 0)):
            t = time.time()
            elem = limits[key]
            if not 'timestamp' in elem or t > elem['timestamp']:
                elem['timestamp'] = t + (elem['cooldown'] if 'cooldown' in elem else cool_down_time)
                ret = str(count) + p_or_ps(count) + ' in ' + name + '\n'
    return ret

def print_iz(name, items):
    if items['val'] > 0:
        print(name + ': ' + str(items['val']) + p_or_ps(items['val']))
        x = json.loads(items['val_s'])
        for item in x:
            c = item['c']
            if c > 0:
                print('	' + time.strftime('%d.%m.%Y', time.localtime(item['d'])) + ': ' + str(c))
        print()

def check_json(js, key, dict):
    for elem in dict:
        if not elem in js:
            print('{0} not in dict for key {1}: {2}'.format(elem, key, js))
            return False
    return True

def scan_iz(auth, id, l = None):
    request = http.request('GET', iz_url)
    try:
        js = json.loads(request.data.decode('utf-8'))
        dict = js['response']['data']
    except JSONDecodeError as err:
        print('caught JSONDecodeError: {0}'.format(err))
        return
    except:
        print('caught unspecific error:')
        print(js)
        return

    tele_msg = ''
    for key in dict.keys():
        if not check_json(dict[key], key, ['name', 'counteritems']) or not \
                check_json(dict[key]['counteritems'][0], key, ['val', 'val_s']):
            continue

        name = dict[key]['name']
        items = dict[key]['counteritems'][0]

        if l:
            msg = in_limits(name, items['val'])
            if (msg):
                print_iz(name, items)
                tele_msg += msg
        else:
            print_iz(name, items)

    if tele_msg:
        send_telegram_message(auth, id, tele_msg)

limits = {
    #'Annaberg' :  { 'limit' :  0, },
    #'Belgern' :   { 'limit' :  0, },
    #'Borna' :     { 'limit' :  0, },
    #'Eich' :      { 'limit' :  0, },
    #'Plauen' :    { 'limit' :  0, },
    'Chemnitz' :  { 'limit' : 10, },
    'Dresden' :   { 'limit' : 10, },
    'Grimma' :    { 'limit' : 20, },
    'Kamenz' :    { 'limit' : 10, },
    'Leipzig' :   { 'limit' : 10, },
    'Löbau' :     { 'limit' : 30, },
    'Mittweida' : { 'limit' : 10, },
    'Pirna' :     { 'limit' : 10, },
    'Riesa' :     { 'limit' : 10, },
    'Zwickau' :   { 'limit' : 20, },
}

parser = argparse.ArgumentParser()
parser.add_argument('--oneshot', '-1', action='store_true', help='print *all* vacant spots and exit, no telegram message')
parser.add_argument('--recipient', '-r', action='store', help='telegram id of the recipient')
parser.add_argument('--bot-auth', '-a', action='store', help='auth string of telegram bot')
args = parser.parse_args()

if False == args.oneshot and (not args.recipient or not args.bot_auth):
    print('non-oneshot mode requires telegram recipient and bot auth\n', file = sys.stderr)
    parser.print_help()
    exit(-1);
elif True == args.oneshot:
    scan_iz(None, None)
    exit(0)

i = 0
while True:
    i = i + 1
    print('executing run #' + str(i), end = '\r')
    # if run without argument, the script prints all venues with vacant
    # vaccination spots and does not generate a telegram message
    scan_iz(args.bot_auth, args.recipient, limits)
    time.sleep(sleep_interval)
