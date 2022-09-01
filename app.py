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
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, Session, relationship

from model import PathInfo, BaseClass, PathInfoEntry
from db import get_db_engine, db_session

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description='Erigon monitor params')
parser.add_argument('--db', dest="db", type=str, help='sqlite or postgres', default="sqlite")
parser.add_argument('--host', dest="host", type=str, help='Host name', default="127.0.0.1")
parser.add_argument('--port', dest="port", type=int, help='Port number', default="5000")
parser.add_argument('--interval', dest="interval", type=int, help='Log scanning interval', default="30")
parser.add_argument('--path', dest="path", type=str, help='Path to be monitored', default=".")
parser.set_defaults(dumpjournal=True)

args = parser.parse_args()

app = Flask(__name__)
cors = CORS(app)


class ProcessClass:
    def __init__(self, path_info):
        self._path_info = path_info
        self._p = Process(target=self.run, args=())
        self._p.daemon = True
        self._p.start()
        pass

    def wait(self):
        self._p.join()

    def run(self):
        size_history = {}
        db_engine = get_db_engine()
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
                with Session(db_engine) as session:
                    session.add(PathInfoEntry(path_info=self._path_info.id, total_size=total_size, files_checked=number_of_files_found, files_failed=number_of_files_failed))
                    session.commit()

            except Exception as ex:
                logger.error(f"Failure when checking directory size: {ex}")

            time.sleep(args.interval)


@app.route('/')
def hello():
    print("test")
    return 'Hello, World!'


@app.route('/html')
def html():
    return render_template('plot.html', sizes_url=url_for("sizes"))


@app.route('/htmltest')
def htmltest():
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


def main():
    db = get_db_engine()
    BaseClass.metadata.create_all(db)

    res = db_session.query(PathInfo).filter_by(path=args.path).all()

    if not res:
        pi = PathInfo(path=args.path)
        db_session.add(pi)
        db_session.commit()
        res = db_session.query(PathInfo).filter_by(path=args.path).all()

    if len(res) == 0:
        raise Exception("Cannot get or create PathInfo object")
    if len(res) > 1:
        logger.warning("More than one PathInfo object found")

    path_info = res[0]
    begin = ProcessClass(path_info)

    app.run(host=args.host, port=args.port, debug=True, use_reloader=False)
    begin.wait()

if __name__ == "__main__":
    main()

