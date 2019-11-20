#!/usr/bin/env python

import argparse
from functools import reduce
import json
import logging
import os
import sys
import toml
import yaml
from datetime import date, datetime, timedelta

class Monitors:
    def __load_datadog_credentials(self):
        try:
            with open('datadog.credentials') as file:
                creds = file.read()
            return (True, creds)
        except Exception as e:
            logging.error(e)
            return (False, '')

    def __init__(self, args, config):
        self.args = args
        self.config = config
        credentials_maybe = self.__load_datadog_credentials()
        if credentials_maybe[0]:
            self.datadog_credentials = credentials_maybe[1]
        else:
            logging.error('Datadog credentials cannot be loaded')
            exit(1)
        logging.debug('Args: %s Config: %s', args, config)

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

def safe_load_yaml(file_name):
    try:
        with open(file_name) as file:
            data = yaml.safe_load(file)
        return (True, data)
    except Exception as e:
        logging.error('Cannot load file: {} because of {}'.format(file_name, e))
        return (False, '')
    
def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)

def deploy_monitors(args, config):
    monitor_types = config.get('monitor-types', {})
      
    if monitor_types.get(args.monitor_type, None):
        logging.info('Monitor type: {monitor_type} is found in the config.'.format(
            monitor_type=args.monitor_type))
    else:
        logging.error('Monitor type is not found in the config.')
        exit(1)

    monitor_types_to_be_deployed = []
    if args.monitor_type == 'all':
        monitor_types.pop('all', None)
        monitor_types_to_be_deployed = list(monitor_types.keys())
    else:
        monitor_types_to_be_deployed.append(args.monitor_type)

    applications_to_be_deployed = []
    if args.application:
        applications_to_be_deployed.append(args.application)
    else:
        path = os.path.join('infra', args.region, args.stage)
        for dir in os.listdir(path):
            application_dir = os.path.join(path, dir)
            if os.path.isdir(application_dir):
                applications_to_be_deployed.append(dir)

    region_path = os.path.join('infra', args.region, 'region.yaml')
    load_region_config = safe_load_yaml(region_path)
    if load_region_config[0]:
        region_config = load_region_config[1]
    else:
        logging.error('Could not load region.yaml')

    stage_path = os.path.join('infra', args.region, args.stage, 'stage.yaml')
    load_stage_config = safe_load_yaml(stage_path)
    if load_stage_config[0]:
        stage_config = load_stage_config[1]
    else:
        logging.error('Could not load stage.yaml')
  
    for application in applications_to_be_deployed:
        application_path = os.path.join('infra', args.region, args.stage, application, 'application.yaml')
        load_yaml_maybe = safe_load_yaml(application_path)
        if load_yaml_maybe[0]:
            application_config = load_yaml_maybe[1]
        else:
            logging.error('Could not load application.yaml')
            break
        for monitor_type in monitor_types_to_be_deployed:
            logging.info('{} {} {} {}'.format(args.region, args.stage, application, monitor_type))
            monitor_type_configs_location_maybe = application_config.get('{}_configs_location'.format(monitor_type), None)
            if monitor_type_configs_location_maybe:
                logging.info(monitor_type_configs_location_maybe)
                if monitor_type_configs_location_maybe == 'region':
                    monitor_type_configs = region_config.get('{}_configs'.format(monitor_type), None)
                elif monitor_type_configs_location_maybe == 'stage':
                    monitor_type_configs = stage_config.get('{}_configs'.format(monitor_type), None)
                elif monitor_type_configs_location_maybe == 'application':
                    monitor_type_configs = application_config.get('{}_configs'.format(monitor_type), None)
                else:
                    logging.error('Monitoring config {} cannot be found'.format(monitor_type))
                    break
            else:
                logging.error('Monitoring config {} cannot be found'.format(monitor_type))
                break
            
            logging.info(monitor_type_configs)
            
            monitor_type_class = monitor_types.get(monitor_type, None)
            if monitor_type_class:
                cls = str_to_class(monitor_type_class)
                cls(args,config).create_monitor()
            else:
                logging.error('Cannot find class for monitor type: {}'.format(monitor_type))


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
