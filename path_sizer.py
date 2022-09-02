from datetime import datetime
import time
from multiprocessing import Process
import logging
import os
from sqlalchemy.orm import Session

from db import db_engine
from model import PathInfoEntry

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DirectoryCheckJob:
    def __init__(self, path_info):
        self._path_info = path_info
        pass

    def run(self):
        folder = self._path_info.path

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
        start = time.time()
        path_info_entry = PathInfoEntry(path_info=self._path_info.id,
                                        total_size=total_size,
                                        files_checked=number_of_files_found,
                                        files_failed=number_of_files_failed)
        with Session(db_engine) as session:
            session.add(path_info_entry)
            session.commit()
        end = time.time()
        logger.info(f"DB insert time: {end - start:0.3f}s")


class ProcessClass:
    def __init__(self, interval, jobs):
        self._interval = interval
        self._jobs = jobs
        self._p = Process(target=self.run, args=())
        self._p.daemon = True
        self._p.start()
        pass

    def wait(self):
        self._p.join()

    def run(self):
        while True:
            try:
                for job in self._jobs:
                    job.run()
            except Exception as ex:
                logger.error(f"Failure when running job {job}: {ex}")

            time.sleep(self._interval)