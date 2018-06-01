#!/usr/bin/env python
#-*-encoding:UTF-8-*-
import os
import sys
import math
from Queue import Queue
sys.path.append(r"../lisa/src")
from lisa import App, route, wserver, redirect
from provider.douban import Provider, Db
import json

wq = Queue(2)

@route('/over')
def over():
    if os.path.exists('./doing'):
        return '{"code":1}'
    else:
        return '{"code":0}'

@route('/refresh')
def refresh():
    print 'set refresh flag'
    wq.put(1)
    try:
        os.mkdir('./doing')
    except Exception, e:
        pass
    print 'refresh msg send over'
    return '{}'

@route('/photos')
def photos():
    db = Db()
    album_id = wserver.req.params['album_id']
    response = {
        'title':'Merlin..',
        'id': album_id,
        'data':[]
    }
    print response
    res = list(db.get('select id, name, src, url from image where album_id = {0}'.format(album_id)))
    print res
    for row in res:
        print row
        response['data'].append({
            'pid':row[0],
            'alt':row[1],
            'src':row[2] if row[2] else row[3]
        })
    
    return json.dumps(response)

@route('/album')
def album():
    db = Db()

    page = wserver.req.params['page']
    print page
    response = {'pages':0, 'data':[]}
    pages = get_pages(db, 'album')
    if pages == 0:
        return json.dumps(response)

    response['pages'] = pages
    sql = 'select id,name,author_id from album order by id desc limit 8 offset ' + \
        str((int(page)-1) * 8)
    res = list(db.get(sql))
    print '-----res.data.len', len(res)
    for row in res:
        response['data'].append({
            'id':row[0],
            'name':row[1],
            'author_id':row[2],
            'cover': get_cover(db, row[0], row[2])
        })
    # print response
    return json.dumps(response)
    

def get_cover(db, album_id, author_id):
    res = db.get('select src from image where album_id = {0} and src != "" limit 1'.format(album_id))
    for row in res:
        return row[0]
    
    res = db.get('select avatar_src from author where id = {0}'.format(author_id))
    for row in res:
        return row[0]

def get_pages(db, table_name):
    res = db.get('select count(*) from {0}'.format(table_name))
    for row in res:
        return math.ceil(float(row[0])/8)
    return 0        
    

def main():
    app = App(title="Merlin", width=900, height=520, icon="./client/Merlin.ico", frameless=False)
    client_path = "file://" + os.getcwd() + "/client/index.html"
    app.init(client_path, debug=True)
    p = Provider(wq)
    p.setDaemon(True)
    p.start()

    app.run()


if __name__ == '__main__':
    main()
