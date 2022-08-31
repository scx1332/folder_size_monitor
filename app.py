import time

from flask import Flask, render_template, url_for
from flask_cors import CORS, cross_origin
from flask import request
import json
import os
import shutil
import argparse
import logging
from multiprocessing import Process
from datetime import datetime

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description='Erigon monitor params')
parser.add_argument('--no-dump-journal', dest="dumpjournal", action='store_false', help='No journal dump for debugging')
parser.add_argument('--host', dest="host", type=str, help='Host name', default="127.0.0.1")
parser.add_argument('--port', dest="port", type=int, help='Port number', default="5000")
parser.add_argument('--interval', dest="interval", type=int, help='Log scanning interval', default="30")
parser.add_argument('--path', dest="path", type=str, help='Path to be monitored', default=".")
parser.set_defaults(dumpjournal=True)

args = parser.parse_args()

app = Flask(__name__)
cors = CORS(app)


class ProcessClass:
    def __init__(self):
        p = Process(target=self.run, args=())
        p.daemon = True                       # Daemonize it
        p.start()                             # Start the execution
        pass

    def run(self):
        size_history = {}

        if os.path.exists("size_history.json"):
            with open("size_history.json", "r") as r:
                size_history = json.loads(r.read())
        while True:
            try:
                folder = args.path

                total_size = 0
                number_of_files_found = 0
                number_of_files_failed = 0
                for path, dirs, files in os.walk(folder):
                    for f in files:
                        fp = os.path.join(path, f)
                        try:
                            total_size += os.path.getsize(fp)
                            number_of_files_found += 1
                        except IOError as err:
                            number_of_files_failed += 1
                            logger.error(f"Error getting size of {fp}: {err}")
                            pass

                logger.info(f"Total size of directory {folder} {total_size})")
                size_history[datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")] = {
                    "path_size": total_size,
                    "files_found": number_of_files_found,
                    "files_failed": number_of_files_failed
                }
                with open("size_history_tmp.json", "w") as w:
                    w.write(json.dumps(size_history, indent=4, default=str))
                shutil.move("size_history_tmp.json", "size_history.json")

            except Exception as ex:
                logger.error(f"Failure when checking directory size: {ex}")

            time.sleep(args.interval)


@app.route('/')
def hello():
    print("test")
    return 'Hello, World!'


@app.route('/html')
def html():
    return render_template('plot.html', sizes_url="http://51.38.53.113:5000/sizes")


@app.route('/sizes')
@cross_origin()
def sizes():
    global events_history

    with open("size_history.json", "r") as f:
        resp = app.response_class(
            response=f.read(),
            status=200,
            mimetype='application/json'
        )
    return resp


if __name__ == "__main__":
    print("test")
    begin = ProcessClass()

    app.run(host=args.host, port=args.port, debug=True, use_reloader=False)
