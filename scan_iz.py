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
    print(f'sending request "{uri}"')
    request = http.request('GET', uri)

def p_or_ps(count):
    return ' freier Platz' if (1 == count) else ' freie Plätze'

def get_total(items, date):
    total = 0
    for item in items:
        if item['d'] >= date and item['c'] > 0:
            total += item['c']
    return total

def get_text(name, items, date):
    ret = name + ':\n'
    for item in items:
        if item['d'] >= date and item['c'] > 0:
            ret += ('\t' + time.strftime('%d.%m.%Y', time.localtime(item['d'])) + ': ' + str(item['c']) + '\n')
    return ret

def print_iz(name, items, l):
    for key in l.keys():
        if key in name:
            total = get_total(items, l[key]['start_date'])
            if 0 < total:
                print(get_text(name, items, l[key]['start_date']))

def in_limits(name, items, l):
    msg = None
    for key in l.keys():
        if key in name:
            total = get_total(items, l[key]['start_date'])
            limit = l[key]['limit']
            if ((limit > 0 and total >= limit) or (limit == 0 and total > 0)):
                t = time.time()
                elem = l[key]
                if not 'timestamp' in elem or t > elem['timestamp']:
                    elem['timestamp'] = t + (elem['cooldown'] if 'cooldown' in elem else cool_down_time)
                    msg = str(total) + p_or_ps(total) + ' in ' + name + '\n'
    return msg

def check_json(js, key, dict):
    for elem in dict:
        if not elem in js:
            print('{0} not in dict for key {1}: {2}'.format(elem, key, js))
            return False
    return True

def scan_iz(l, auth = None, id = None):
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

        if 0 < items['val']:
            j = json.loads(items['val_s'])
            if id and auth:
                msg = in_limits(name, j, l)
                if (msg is not None):
                    tele_msg += msg
            else:
                msg = ''
            if msg is not None:
                print_iz(name, j, l)

    if tele_msg:
        print(time.asctime((time.gmtime(int(time.strftime("%s", time.gmtime()))+3*3600))), end = ": \n")
        send_telegram_message(auth, id, tele_msg)

def main():
    limits = {
        #'Annaberg' :  { 'limit' :  0, },
        #'Belgern' :   { 'limit' :  0, },
        #'Borna' :     { 'limit' :  0, },
        #'Eich' :      { 'limit' :  0, },
        #'Plauen' :    { 'limit' :  0, },
        'Chemnitz' :  { 'limit' : 10, },
        'Dresden' :   { 'limit' : 10, },
        'Grimma' :    { 'limit' : 10, },
        'Kamenz' :    { 'limit' : 10, },
        'Leipzig' :   { 'limit' : 10, },
        'Löbau' :     { 'limit' : 10, },
        'Mittweida' : { 'limit' : 10, },
        'Pirna' :     { 'limit' : 10, },
        'Riesa' :     { 'limit' : 10, },
        'Zwickau' :   { 'limit' : 10, },
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--oneshot', '-1', action='store_true', help='print *all* vacant spots and exit, no telegram message')
    parser.add_argument('--recipient', '-r', action='store', help='telegram id of the recipient')
    parser.add_argument('--bot-auth', '-a', action='store', help='auth string of telegram bot')
    parser.add_argument('--start-date', '-d', action='store', help='only consider vacant spots after this date, format dd.mm')
    args = parser.parse_args()

    if args.start_date is None:
        t = time.mktime(time.localtime())
    else:
        t = round(time.mktime(time.strptime(args.start_date + '2021', '%d.%m.%Y')))

    for key in limits.keys():
        if 'start_date' not in limits[key]:
            limits[key]['start_date'] = t

    if False == args.oneshot and (not args.recipient or not args.bot_auth):
        print('non-oneshot mode requires telegram recipient and bot auth\n', file = sys.stderr)
        parser.print_help()
        exit(-1);
    elif True == args.oneshot:
        scan_iz(limits)
        exit(0)

    i = 0
    while True:
        i = i + 1
        print('executing run #' + str(i), end = '\r')
        # if run without argument, the script prints all venues with vacant
        # vaccination spots and does not generate a telegram message
        scan_iz(limits, args.bot_auth, args.recipient)
        time.sleep(sleep_interval)

if __name__ == '__main__': main()
