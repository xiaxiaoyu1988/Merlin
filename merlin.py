#!/usr/bin/env python
#-*-encoding:UTF-8-*-
import os
import sys

sys.path.append(r"../lisa/src")
from lisa import App, route, wserver, redirect


@route('/photos')
def photos():
	print 'photos'
	return '''{
            "title": "", 
            "id": 123, 
            "start": 0,
  			"data": [ 
            {
                "alt": "图片名1",
                "pid": 666, 
                "src": "http://s17.mogucdn.com/p2/161011/upload_279h87jbc9l0hkl54djjjh42dc7i1_800x480.jpg", 
                "thumb": "" 
            },
			{
                "alt": "图片名2",
                "pid": 667, 
                "src": "http://s17.mogucdn.com/p2/161011/upload_279h87jbc9l0hkl54djjjh42dc7i1_800x480.jpg", 
                "thumb": "" 
            }
           ]
        }'''


def main():
    app = App(title="Merlin", width=900, height=520, icon="./client/Merlin.ico")
    client_path = "file://" + os.getcwd() + "/client/index.html"
    app.init(client_path, debug=True)
    app.run()


if __name__ == '__main__':
    main()
