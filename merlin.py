import os
import sys

sys.path.append(r"./Lisa/src")
from lisa import App, route, wserver, redirect


@route('/login')
def login():
	username = wserver.req.params['username']
	password = wserver.req.params['password']
	if username == 'admin' and password == '123':
		return '{"code":0}'
	else:
		return '{"code":1}'


def main():
    app = App(title="Merlin", width=900, height=520, icon="./client/Merlin.ico")
    client_path = "file://" + os.getcwd() + "/client/index.html"
    app.init(client_path, debug=True)
    app.run()


if __name__ == '__main__':
    main()
