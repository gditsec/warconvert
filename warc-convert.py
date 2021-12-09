#-*- coding : utf-8-*-

import sys, os
import datetime
import base64, json
import hashlib
from xml.dom.minidom import parse
from har2warc.har2warc import har2warc


def http2json(http, isResponse, url):
    ret = {}
    pos = http.find('\r\n\r\n'.encode('utf-8'))
    body = http[pos + 4:]
    # body有可能是二进制文件，如图片、视频，此时会decode出错，这里采用base64的方式解决
    body = base64.encodebytes(body).decode('utf-8')
    http = http[:pos].decode('utf-8')
    http = http.split('\r\n')
    if isResponse:
        bodyLength = 0
        bodyType = ''
        http[0] = http[0].split(' ')
        ret['status'] = http[0][1]
        ret['statusText'] = http[0][2]
        ret['httpVersion'] = http[0][0]
        ret['headers'] = []
        for header in http[1:]:
            if len(header) > 0:
                header = header.split(': ')
                ret['headers'].append({
                    'name': header[0],
                    'value': header[1]
                })
                if header[0] == 'Content-Length':
                    bodyLength = header[1]
                if header[0] == 'Content-Type':
                    bodyType = header[1]
        ret['bodySize'] = bodyLength
        ret['content'] = {
            'size': bodyLength,
            'mimeType': bodyType,
            'text': body,
            'encoding': 'base64'
        }
        return ret
    else:
        http[0] = http[0].split(' ')
        ret['method'] = http[0][0]
        ret['url'] = url
        ret['httpVersion'] = http[0][2]
        ret['headers'] = []
        ret['bodySize'] = -1
        for header in http[1:]:
            if len(header) > 0:
                header = header.split(': ')
                ret['headers'].append({
                    'name': header[0],
                    'value': header[1]
                })
        return ret


def main(filename, outfile):
    print('Loading XML file...')
    DOMTree = parse(filename)
    collection = DOMTree.documentElement

    items = collection.getElementsByTagName('item')

    harContent = {
        'log': {
            'pages': [],
            'entries': [],
            'creator': {
                'name': 'gditsec',
                'version': '1.0'
            },
            'version': '1.0'
        }
    }

    for item in items:
        startedTime = datetime.datetime.strptime(item.getElementsByTagName('time')[0].childNodes[0].data, "%a %b %d %H:%M:%S CST %Y")
        startedTime = startedTime.strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            'startedDateTime': startedTime,
            'time': 0,
            'request': {},
            'response': {},
            'cache': {
                'beforeRequest': {},
                'afterRequest': {},
                'comment': ''
            },
            'timeings': {
                'blocked': 0,
                'dns': 0,
                'connect': 0,
                'send': 0,
                'wait': 0,
                'receive': 0,
                'ssl': 0
            },
            'pageref': ''
        }
        url = item.getElementsByTagName('url')[0].childNodes[0].data
        req = item.getElementsByTagName('request')[0]
        if req.getAttribute('base64'):
            req = base64.decodestring(req
                        .childNodes[0].data.encode('utf-8'))
            req = http2json(req, False, url)
        else:
            req = http2json(req.childNodes[0].data.encode('utf-8'), False, url)
        res = item.getElementsByTagName('response')[0]
        if res.getAttribute('base64'):
            res = base64.decodestring(res
                        .childNodes[0].data.encode('utf-8'))
            res = http2json(res, True, url)
        else:
            res = http2json(res.childNodes[0].data.encode('utf-8'), True, url)
        entry['response'] = res
        entry['request'] = req
        harContent['log']['entries'].append(entry)
        harContent['log']['pages'].append({
            'startedDateTime': startedTime,
            'id': url,
            'title': url
        })
    print('Finished.')
    print('Converting to har file...')
    with open('tmp.har', 'w') as harFile:
        harFile.write(json.dumps(harContent))
    print('Finished.')
    print('Converting to warc file...')
    har2warc('tmp.har', outfile)
    # os.unlink('tmp.har')
    print('Finished.')


if __name__ == '__main__':
    banner = '''
====================================
 __      ____ _ _ __ ___ ___ _ __ 
 \ \ /\ / / _` | '__/ __/ _ \ '__|
  \ V  V / (_| | | | (_|  __/ |   
   \_/\_/ \__,_|_|  \___\___|_|
====================================

    '''
    print(banner)
    if len(sys.argv) == 0 or len(sys.argv) != 3 or sys.argv[1] == '-h':
        print('usage: python warc-convert.py xmlfile.xml outfile.warc')
    else:
        main(sys.argv[1], sys.argv[2])