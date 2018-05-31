#!/usr/bin/env python
#-*-encoding:UTF-8-*-

import requests as r
import time
import datetime
import threading
import sqlite3
from pyquery import PyQuery as pq
from Queue import Queue
import os
import sys
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

PEOPLE_PATH = './people/'

AUTHOR_INSERT = 'INSERT INTO "main"."author" ("username", "add_time", "avatar", "location", "comment", "url", "user_id") VALUES("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}")'
ALBUM_INSERT = 'INSERT INTO "main"."album" ("name", "author_id", "datetime", "url") VALUES ("{0}", "{1}", "{2}", "{3}");'
IMAGE_INSERT = 'INSERT INTO "main"."image" ("name", "author_id", "album_id", "src", "url") VALUES ("{0}", "{1}", "{2}", "{3}", "{4}");'

class Provider(threading.Thread):
    def __init__(self):
        super(Provider, self).__init__()
        self.url = 'https://www.douban.com/group/haixiuzu/discussion?start='
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'DNT': '1',
            'Referer': 'https://www.douban.com/group/haixiuzu/discussion',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': 'bid=yT-TsYOa0Kg; __yadk_uid=Azbbpz5GZnARPeQTj29AY9NCJygBErNm; ll="108184"; _vwo_uuid_v2=D587455F45EDD061C48289E2A77C7AC6E|b52e16a4989e2cd17f62429841bb3a57; __utmc=30149280; __utmz=30149280.1527737279.6.6.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1527759238%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DHrh3mnJ8DAWDcP7X7VyxsvdaofFCtEyewAPlgxYbdpxvREXePjTXje-IYBiyJCS_%26wd%3D%26eqid%3Dc29264ee0000358a000000055b0f6bbe%22%5D; _pk_ses.100001.8cb4=*; __utma=30149280.557746954.1524814907.1527753482.1527759240.10; __utmt=1; as="https://www.douban.com/group/haixiuzu/discussion?start=0"; ps=y; _pk_id.100001.8cb4=494ca7a09b021e0a.1524814906.10.1527760921.1527753836.; __utmb=30149280.79.5.1527760922075'}
        self.dq = Queue(300)
        self.downer = Downloader(self.dq)
        self.downer.setDaemon(True)
        self.downer.start()
    def run(self):
        self.db = Db()

        while 1:
            try:
                time.sleep(1)
                last_date = self.db.get_last_date()
                current_date = str(datetime.date.today())
                # first use
                if not last_date:
                    last_date = str(datetime.date.today() - datetime.timedelta(days=2))
                elif current_date == last_date:
                    print 'update today, continue'
                    continue
                self.get_all_topic(last_date)
                # TODO:update last_date
                self.db.set('update config set value = "{0}" where name="LAST_DATE"'.format(last_date))
                break
            except Exception, e:
                print '==============ERROR-----------------', str(e)
                break


    def get_all_topic(self, last_date):
        print last_date
        current_year = last_date.split('-')[0]
        for i in range(10):
            print '=========ALL=========', self.url + str(i)
            res = r.get(self.url + str(i), headers = self.headers, verify=False)
            # res = open('./1.html').read()
            if res:
                # print len(res)
                if res.status_code != 200:
                    continue
                doc = pq(res.content)
                for tr in doc('tr'):
                    _tr = pq(tr)
                    atags = _tr('a')
                    if len(atags) < 2:
                        continue
                    topic_datetime = _tr('.time').text()
                    topic_date = current_year + '-' + topic_datetime.split()[0]
                    if datetime.datetime.strptime(topic_date, '%Y-%m-%d') <= datetime.datetime.strptime(last_date, '%Y-%m-%d'):
                        print topic_date, ' <= ', last_date
                        return

                    topic_a = pq(atags[0])
                    topic_href = topic_a.attr('href')
                    topic_title = topic_a.attr('title')
                    if u'【晒】' not in topic_title:
                        print 'no pic'
                        continue
                    print "--------item--------", topic_title

                    topic_title = topic_title.replace(u'【晒】', '')
                    
                    author_a = pq(atags[1])
                    author_href = author_a.attr('href')
                    author_name = author_a.text()
                    print author_name, topic_datetime, topic_title

                    author_id, author_dir = self.author(
                        author_name, author_href)
                    print 'author_id', author_id, author_dir
                    if author_id:
                        print '-----------handle-----', topic_href
                        self.topic(author_id, topic_title, topic_href,
                                   current_year + '-' + topic_datetime, author_dir)
                # print res.status_code, type(res.status_code)
                # if res.status_code == 200:
                    # content = res.content.decode('utf8', "replace")
                    # doc = pq(res.content)
                    # print doc(".olt")
                # break
            time.sleep(1)
    
    def author(self, author_name, author_href):
        #is author exists
        author_id, author_dir = self.db.is_author_exists(author_href)
        if not author_id:
            print 'req author info'
            res = r.get(author_href, headers=self.headers, verify=False)
            print 'req author info complete'
            if res:
                if res.status_code == 200:
                    doc = pq(res.content)
                    location = doc('.user-info')('a').text()
                    user_info = doc('.user-info')('.pl').text() 
                    user_id = str(user_info.split('\n')[0])
                    add_time = ''.join(user_info.split('\n')[1:])
                    avatar = doc('.userface').attr('src')
                    comment = doc('.intro_display').text()

                    print author_name, type(author_name)
                    if type(author_name) is unicode:
                        author_name = author_name.encode('utf8', 'replace')
                    print add_time, type(add_time)
                    if type(add_time) is unicode:
                        add_time = add_time.encode('utf8')
                    print avatar, type(avatar)
                    print type(location)
                    if type(location) is unicode:
                        location = location.encode('utf8')
                    print comment, type(comment)
                    print user_id, type(user_id)
                    
                    print '--insert author'
                    author_id = self.db.set(AUTHOR_INSERT.format(
                        str(author_name)
                        , str(add_time), str(avatar)
                        , str(location), str(comment), str(author_href)
                        , str(user_id))
                        )

                    author_dir = PEOPLE_PATH + str(author_id)
                    avatar_src=author_dir + '/avatar.jpg'

                    print author_dir
                    print avatar_src

                    self.init_dir(author_dir)
                    print '---in download'
                    self.dq.put(
                        {'type': 'author', 'author_id': author_id, 'src': avatar, 'location': avatar_src})

        return author_id, author_dir

    def init_dir(self, dir_name):
        if not os.path.exists("./client/" + dir_name):
            os.mkdir("./client/" + dir_name)
    
    def topic(self, author_id, topic_title, topic_href, topic_datetime, author_dir):
        topic_title = topic_title.encode('utf8')
        print type(topic_title)
        print type(topic_href)
        print type(topic_datetime)
        topic_datetime = topic_datetime.replace('-', '').replace(' ', '').replace(':', '')
        if self.db.is_album_exists(topic_datetime):
            print '-------album_exists'
            return
        album_id = self.db.set(ALBUM_INSERT.format(topic_title, author_id, topic_datetime, topic_href))
        print 'album_id-', album_id
        download_path = author_dir + '/' + topic_datetime + '/'
        self.init_dir(download_path)
        res = r.get(topic_href, headers=self.headers, verify=False)
        if res:
            print '------', res.status_code
            if res.status_code == 200:
                doc = pq(res.content)
                imgs = []
                print doc('#link-report')('.topic-content')('img')
                for img in doc('#link-report')('.topic-content')('img'):
                    _img = pq(img)
                    imgs.append(_img.attr('src'))
                print '-------', imgs
                self.dq.put({"type": 'topic','download_path':download_path, 'imgs':imgs, 'name':topic_title, 'author_id':author_id, 'album_id':album_id})


class Downloader(threading.Thread):
    def __init__(self, dq):
        super(Downloader, self).__init__()
        self.dq = dq
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'DNT': '1',
            'Referer': 'https://www.douban.com/group/haixiuzu/discussion',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': 'bid=yT-TsYOa0Kg; __yadk_uid=Azbbpz5GZnARPeQTj29AY9NCJygBErNm; ll="108184"; _vwo_uuid_v2=D587455F45EDD061C48289E2A77C7AC6E|b52e16a4989e2cd17f62429841bb3a57; __utmc=30149280; __utmz=30149280.1527737279.6.6.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1527759238%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DHrh3mnJ8DAWDcP7X7VyxsvdaofFCtEyewAPlgxYbdpxvREXePjTXje-IYBiyJCS_%26wd%3D%26eqid%3Dc29264ee0000358a000000055b0f6bbe%22%5D; _pk_ses.100001.8cb4=*; __utma=30149280.557746954.1524814907.1527753482.1527759240.10; __utmt=1; as="https://www.douban.com/group/haixiuzu/discussion?start=0"; ps=y; _pk_id.100001.8cb4=494ca7a09b021e0a.1524814906.10.1527760921.1527753836.; __utmb=30149280.79.5.1527760922075'}

    def run(self):
        self.db = Db()
        while  1:
            try:
                item = self.dq.get(True)
                if item['type'] == 'author':
                    if self.download_file(item['src'], item['location']):
                        self.db.set('update author set avatar_src = "{0}" where id = "{1}"'.format(item['location'], item['author_id']))
                elif item['type'] == 'topic':
                    for url in item['imgs']:
                        dst = item['download_path'] + url.split('/')[-1]
                        if self.download_file(url, dst):
                            self.db.set(IMAGE_INSERT.format(
                                item['name'], item['author_id'], item['album_id'], dst, url))
            except Exception, e:
                print str(e)

    def download_file(self, url, dst):
        try:
            dst = './client/' + dst
            if not url:
                return False
            res = r.get(url, headers=self.headers, stream=True, verify=False)
            if res:
                if res.status_code == 200:
                    with(open(dst, 'ab')) as f:
                        for chunk in res.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    return True
        except Exception, e:
            print str(e)
        


class Db(object):
    def __init__(self, db_path = './merlin.db'):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
    
    def get(self, sql):
        # print sql
        return self.c.execute(sql)
    
    def set(self, sql):
        print sql
        self.c.execute(sql)
        self.conn.commit()
        res = self.get('SELECT last_insert_rowid()')
        if res:
            for row in res:
                return row[0]

    def get_last_date(self):
        res = self.get('select value from config where name = "LAST_DATE"')
        for row in res:
            return row[0]
    
    def is_author_exists(self, author_href):
        res = self.get('select id from author where url = "{0}"'.format(author_href))
        for row in res:
            return row[0], PEOPLE_PATH + str(row[0])
        return (None, None)
    
    def is_album_exists(self, topic_datetime):
        res = self.get('select count(*) as c from album where datetime="{0}"'.format(topic_datetime))
        for row in res:
            if row[0] > 0:
                return True

def main():
    p = Provider()
    p.setDaemon(True)
    p.start()

    while 1:
        time.sleep(1)

if __name__ == '__main__':
    main()
