#!/usr/bin/env python

import argparse
from functools import reduce
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
        logging.info('Args: %s Config: %s', args, config)

    def create_monitor(self):
        pass

class SystemMonitors(Monitors):
    def create_monitor(self):
        logging.info('Creating system monitors')


class AwsElbMonitors(Monitors):
    def create_monitor(self):
        logging.info('Creating AWS ELB monitors')

#############################################################################
################################# main ######################################
#############################################################################

def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)

def deploy_monitors(args, config):
    monitor_types = config.get('monitor-types', {})
    if monitor_types.get(args.monitor_type, None):
        logging.info('Monitor type: {monitor_type} is found in the config.'.format(monitor_type=args.monitor_type))
    else:
        logging.error('Monitor type is not found in the config.')
        exit(1)

    monitor_types_to_be_deployed = []
    if args.monitor_type == 'all':
        monitor_types.pop('all', None)
        monitor_types_to_be_deployed = list(monitor_types.values())
    else:
        monitor_types_to_be_deployed.append(monitor_types.get(args.monitor_type, None))

    for monitor in monitor_types_to_be_deployed:
        cls = str_to_class(monitor)
        cls(args,config)

    applications_to_be_deployed = []
    if args.application:
        applications_to_be_deployed = args.application
    else:
        path = os.path.join('infra', args.region, args.stage)
        for dir in os.listdir(path):
            application_dir = os.path.join(path, dir)
            if os.path.isdir(application_dir):
                with open(os.path.join(application_dir, 'application.yaml')) as file:
                    print(file.read())

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

        deploy_monitors = subparsers.add_parser('deploy-monitors')
        deploy_monitors.add_argument('-r', '--region', action='store', required=True)
        deploy_monitors.add_argument('-s', '--stage', action='store', required=True)
        deploy_monitors.add_argument('-a', '--application', action='store', required=False)
        deploy_monitors.add_argument('-m', '--monitor-type', action='store', required=False)
        deploy_monitors.add_argument_group('deploy-monitors', '')
        deploy_monitors.set_defaults(func='deploy-monitors')

        deploy_dashboards = subparsers.add_parser('deploy-dashboards')
        deploy_dashboards.add_argument('-r', '--region', action='store', required=True)
        deploy_dashboards.add_argument('-s', '--stage', action='store', required=True)
        deploy_dashboards.add_argument('-a', '--application', action='store', required=False)
        deploy_dashboards.add_argument_group('deploy-dashboards', '')
        deploy_dashboards.set_defaults(func='deploy-dashboards')

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
