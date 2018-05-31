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

PEOPLE_PATH = './client/people/'

AUTHOR_INSERT = 'INSERT INTO "main"."author" ("username", "add_time", "avatar", "location", "comment", "url", "user_id") VALUES("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}")'
ALBUM_INSERT = 'INSERT INTO "main"."album" ("name", "author_id", "datetime") VALUES ("{0}", "{1}", "{2}");'
IMAGE_INSERT = 'INSERT INTO "main"."image" ("name", "author_id", "album_id", "src", "thumbnail") VALUES (NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);'

class Provider(threading.Thread):
    def __init__(self):
        super(Provider, self).__init__()
        self.url = 'https://www.douban.com/group/haixiuzu/discussion?start='
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        self.dq = Queue(300)
        self.downer = Downloader(self.dq)
        self.downer.setDaemon(True)
        self.downer.start()
    def run(self):
        self.db = Db()

        while 1:
            time.sleep(1)
            last_date = self.db.get_last_date()
            # first use
            if not last_date:
                last_date = str(datetime.date.today() - datetime.timedelta(days=2))
            self.get_all_topic(last_date)
            break

    def get_all_topic(self, last_date):
        print last_date
        current_year = last_date.split('-')[0]
        for i in range(10):
            # res = r.get(self.url + str(i), headers = self.headers, verify=False)
            res = open('./1.html').read()
            if res:
                print len(res)
                doc = pq(res)
                for tr in doc('tr'):
                    _tr = pq(tr)
                    atags = _tr('a')
                    if len(atags) < 2:
                        continue
                    topic_datetime = _tr('.time').text()
                    topic_date = current_year + '-' + topic_datetime.split()[0]
                    if datetime.datetime.strptime(topic_date, '%Y-%m-%d') < datetime.datetime.strptime(last_date, '%Y-%m-%d'):
                        print topic_date, ' < ', last_date
                        continue

                    topic_a = pq(atags[0])
                    topic_href = topic_a.attr('href')
                    topic_title = topic_a.attr('title')
                    if u'【晒】' not in topic_title:
                        print 'no pic'
                        continue
                    author_a = pq(atags[1])
                    author_href = author_a.attr('href')
                    author_name = author_a.text()
                    print author_name, topic_datetime, topic_title

                    self.author(author_name, author_href)
                    self.topic()
                    break
                # print res.status_code, type(res.status_code)
                # if res.status_code == 200:
                    # content = res.content.decode('utf8', "replace")
                    # doc = pq(res.content)
                    # print doc(".olt")
                break
            time.sleep(1)
    
    def author(self, author_name, author_href):
        #is author exists
        if not self.db.is_author_exists(author_href):
            print 'req author info'
            res = r.get(author_href, headers=self.headers, verify=False)
            print 'req author info complete'
            if res:
                if res.status_code == 200:
                    doc = pq(res.content)
                    location = doc('.user-info')('a').text()
                    user_info = doc('.user-info')('.pl').text() 
                    user_id = user_info.split('\n')[0]
                    add_time = ''.join(user_info.split('\n')[1:])
                    avatar = doc('.userface').attr('src')
                    comment = doc('.intro_display').text()

                    # print author_name, type(author_name)
                    # print add_time, type(add_time)
                    if type(add_time) is unicode:
                        add_time = add_time.encode('utf8')
                    # print avatar, type(avatar)
                    # print type(location)
                    if type(location) is unicode:
                        location = location.encode('utf8')
                    # print comment, type(comment)
                    
                    author_dir = PEOPLE_PATH + user_id
                    avatar_src = author_dir + '/avatar.jpg'
                    self.init_author_dir(author_dir)
                    self.db.set(AUTHOR_INSERT.format(
                        author_name, add_time, avatar, location, comment, author_href, user_id))
                    self.dq.put(
                        {'type': 'author', 'user_id': user_id, 'src': avatar, 'location': avatar_src})
    
    def init_author_dir(self, author_dir):
        if not os.path.exists(author_dir):
            os.mkdir(author_dir)
    
    def topic(self, ):



class Downloader(threading.Thread):
    def __init__(self, dq):
        super(Downloader, self).__init__()
        self.dq = dq
    def run(self):
        while  1:
            item = self.dq.get(True)
            print item

class Db(object):
    def __init__(self, db_path = './merlin.db'):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
    
    def get(self, sql):
        return self.c.execute(sql)
    
    def set(self, sql):
        print sql
        self.c.execute(sql)
        self.conn.commit()

    def get_last_date(self):
        res = self.get('select value from config where name = "LAST_DATE"')
        for row in res:
            return row[0]
    
    def is_author_exists(self, author_href):
        res = self.get('select count(*) as c from author where url = "{0}"'.format(author_href))
        for row in res:
            if row[0] > 0 :
                return True

def main():
    p = Provider()
    p.setDaemon(True)
    p.start()

    while 1:
        time.sleep(1)

if __name__ == '__main__':
    main()
