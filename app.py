from flask import Flask, request, session, render_template, redirect, send_from_directory
from werkzeug.utils import secure_filename
import os
from os.path import isfile, join
import secrets
from hashlib import sha3_512
from threading import Thread


app = Flask(__name__)
app.secret_key = os.urandom(64)
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

SECURE_KEY = "3387382e27d23c4737817e3d05132b750946896ac581dffc174f9dc2e28f5e12984e1f27142d148323f2afc3d8eb28812e8a832198b6af8a08c0169a71a3ee83"


def sha3(msg):
    return sha3_512(msg.encode()).hexdigest()


def get_name(name):
    return "".join(name.split(".")[:-1]).replace("_", " ").title()


def get_display():
    path = "static/core"
    files = [f for f in os.listdir(path) if isfile(join(path, f)) and f.endswith("html")]
    display = []
    for file in files:
        display.append([file, get_name(file), file[:-4] + "md"])
    return display


@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        url = url.replace('5000', '8000')
        print(url)
        code = 301
        return redirect(url, code=code)


@app.route("/", methods=["GET", "POST"])
def validate_user():
    if 'username' in session and request.method == "GET":
        return render_template("files.html", links=get_display())

    if request.method == 'GET':
        return render_template("login.html")

    data = dict(request.form)
    if data["username"] == "exorun" and secrets.compare_digest(sha3(data["password"]), SECURE_KEY):
        session["username"] = data["username"]
        return render_template("files.html", links=get_display())

    return "<h1>Invalid Credentials</h1>", 403


@app.route("/edit/<file>", methods=["GET", "POST"])
def handle_edits(file):
    if 'username' not in session:
        return redirect("/")

    if request.method == "GET":
        text = open(f"static/core/{file}").read()
        return render_template("editor.html", title=get_name(file), filename=file, code=text)

    if request.method == "POST":
        data = dict(request.form)
        if 'title' not in data or 'code' not in data:
            return "<h1>Don't fuck around, you jackass!!</h1>"
        
        file = open(f"static/core/{file}", 'w')
        file.write(data['code'])
        file.close()
        return redirect("/")


@app.route("/create", methods=["GET", "POST"])
def create_note():
    if 'username' not in session:
        return redirect("/")

    if request.method == "GET":
        return render_template("creator.html")

    if request.method == "POST":
        data = dict(request.form)
        if 'title' not in data or 'code' not in data:
            return "<h1>Don't fuck around you, jackass!!</h1>"

        filename = "_".join(data['title'].split(" ")) + ".html"
        filename = secure_filename(filename)
        file = open(f"static/core/{filename}", 'w')
        file.write(data['code'])
        file.close()
        filename = "_".join(data['title'].split(" ")) + ".md"
        filename = secure_filename(filename)
        file = open(f"static/core/{filename}", 'w')
        file.write(data['code'])
        file.close()
        return redirect("/")


@app.route('/download/<file>', methods=['GET'])
def serve_dir_directory_index(file):
    if 'username' not in session:
        return redirect("/")

    return send_from_directory(static_file_dir, f'core/{file}')


@app.route('/logout', methods=['GET'])
def logout():
    if 'username' in session:
        del session['username']
    return redirect('/')


def deploy_http():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)


def deploy_https():
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, ssl_context=('cert.pem', 'key.pem'), threaded=True)


if __name__ == '__main__':
    print("PID:", os.getpid())
    Thread(target=deploy_http).start()
    deploy_https()

# gunicorn --certfile cert.pem --keyfile key.pem -b 0.0.0.0:8000 app:app
