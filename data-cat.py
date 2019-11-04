#!/usr/bin/env python

import argparse
import json
import logging
import os
import sys
import toml
from datetime import date, datetime, timedelta

class Monitors:
    def __init__(self, args, config):
        self.args = args
        self.config = config
        logging.debug('Args: %s Config: %s', args, config)
    
    def create_monitor(self):
        pass

class SystemMonitors(Monitors):
    def create_monitor(self):
        logging.info('Creating system monitors')

        
class AwsElbMonitors(Monitors):
    def create_monitor(self):
        logging.info('Creating AWS ELB monitors')

def deploy_monitors(args, config):
    system_monitors = SystemMonitors(args, config)
    system_monitors.create_monitor()
    aws_elb_monitors = AwsElbMonitors(args, config)
    aws_elb_monitors.create_monitor()
    pass

def deploy_dashboards(args, config):
    pass

def noop(args=None, config=None):
    logging.error('Not implemented function is called')

def args_switch(args, config):
    fn = switcher.get(args.func, noop)
    logging.info('fn: %s', fn)
    return fn(args, config)

switcher = {
    'deploy-monitors': deploy_monitors,
    'deploy-dashboards': deploy_dashboards,
}

def main():
    try:
        exe_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        config = toml.load(os.path.join(exe_path, 'config', 'data-cat.toml'))
        log_folder_relative = config.get('main', {}).get('log_folder', 'logs')
        log_folder_absolute = os.path.join(exe_path, log_folder_relative)
        if not os.path.isdir(log_folder_absolute):
            os.makedirs(log_folder_absolute, 0o750, exist_ok=True)
        today = str(date.today())
        log_handlers = []
        log_handlers.append(logging.FileHandler("{0}/{1}.{2}.log".format(log_folder_absolute, today, os.getpid())))
        log_handlers.append(logging.StreamHandler(sys.stdout))
        logging.basicConfig(
            level=logging.INFO,
            format=config.get('main', {}).get('log_pattern', '%(asctime)s %(levelname)-4s %(message)s'),
            datefmt=config.get('main', {}).get('log_date_fmt', '%Y-%m-%d %H:%M:%S'),
            handlers=log_handlers)
      
        parser = argparse.ArgumentParser(prog='data-cat')
        subparsers = parser.add_subparsers()

        deploy_monitors     = subparsers.add_parser('deploy-monitors')
        deploy_monitors.add_argument('-r', '--region', action='store', required=True)
        deploy_monitors.add_argument('-s', '--stage', action='store', required=True)
        deploy_monitors.add_argument('-a', '--application', action='store', required=False)
        deploy_monitors.add_argument_group('deploy-monitors', '')
        deploy_monitors.set_defaults(func='deploy-monitors')

        args = parser.parse_args()
        
        logging.info('ARGS: %s', args)
        
        if not any(vars(args).values()):
            logging.error("No parameter were passed")
            parser.print_help()
            exit(1)
        else:
            args_switch(args, config)

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
