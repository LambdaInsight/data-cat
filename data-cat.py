#!/usr/bin/env python

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta

class Monitors:
    def __init__(self):
        pass
    def create_monitor(self):
        pass

class SystemMonitors(Monitors):
    def __init__(self):
        pass
    def create_monitor(self):
        pass

class AwsElbMonitors(Monitors):
    def __init__(self):
        pass
    def create_monitor(self):
        pass

def main():
    try:
        exe_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        log_folder_relative = 'logs/'
        log_folder_absolute = os.path.join(exe_path, log_folder_relative)
        if not os.path.isdir(log_folder_absolute):
            os.makedirs(log_folder_absolute, 0o750, exist_ok=True)
        today = str(date.today())
        log_handlers = []
        log_handlers.append(logging.FileHandler("{0}/{1}.{2}.log".format(log_folder_absolute, today, os.getpid())))
        log_handlers.append(logging.StreamHandler(sys.stdout))
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)-4s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=log_handlers)
    except KeyboardInterrupt:
        logging.info("Ctrl+c was pressed, exiting...")
        exit(0)
    except Exception as e:
        logging.error('Exception caught in main')
        logging.error('Exception caught: %s', e)
        exit(1)
    finally:
        logging.info("Quitting...")

if __name__ == '__main__':
    exit(main())
