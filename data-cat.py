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
from datadog import initialize, api

class MonitorDefault(dict):
    def __missing__(self, key):
        return key

class Monitors:
    def __load_datadog_credentials(self):
        try:
            with open('datadog.creds.yaml') as file:
                creds = yaml.safe_load(file)
            return (True, creds)
        except Exception as e:
            logging.error(e)
            return (False, '')

    def __initialize_datadog(self, api_key, app_key):
        try:
            if api_key == 'mock' and app_key == 'mock':
                self.datadog_mock = True
                logging.info('Skipping initializing DataDog')
            else:
                self.datadog_mock = False
                options = {
                    'api_key': api_key,
                    'app_key': app_key,
                    'api_host': 'https://api.datadoghq.eu'
                }
                initialize(**options)
                #logging.info(api.User.get_all())
        except Exception as e:
            logging.error(e)

    def __init__(self, args, config):
        self.args = args
        self.config = config
        credentials_maybe = self.__load_datadog_credentials()

        if credentials_maybe[0]:
            self.__initialize_datadog(
                credentials_maybe[1].get('api_key'),
                credentials_maybe[1].get('app_key'))
        else:
            logging.error('Datadog credentials cannot be loaded')
            exit(1)
        logging.debug('Args: %s Config: %s', args, config)

    def datadog_api_monitor_create(self, monitor_config_tuple):
        try:
            if self.datadog_mock == True:
                logging.info('Mocking the monitor creation')
                return (True, {'mock': 'mock'})
            else:
                response = api.Monitor.create(
                    name    = monitor_config_tuple[0],
                    message = monitor_config_tuple[1],
                    options = monitor_config_tuple[2],
                    query   = monitor_config_tuple[3],
                    tags    = monitor_config_tuple[4],
                    type    = monitor_config_tuple[5]
                )
                return (True, response)
        except Exception as e:
            logging.error(e)
            return (False, str(e))

    def datadog_api_monitor_update(self, monitor_config_tuple, monitor_id):
        try:
            if self.datadog_mock == True:
                logging.info('Mocking the monitor creation')
                return (True, {'mock': 'mock'})
            else:
                response = api.Monitor.update(
                    monitor_id,
                    name    = monitor_config_tuple[0],
                    message = monitor_config_tuple[1],
                    options = monitor_config_tuple[2],
                    query   = monitor_config_tuple[3],
                    tags    = monitor_config_tuple[4],
                    type    = monitor_config_tuple[5]
                )
                return (True, response)
        except Exception as e:
            logging.error(e)
            return (False, str(e))

    def get_template_file_name(self, monitor_type, monitor_subtype):
        return os.path.join('templates', monitor_type, '{}.yaml'.format(monitor_subtype))


    def render_template(self, region, stage, application_name, default_configs, monitor_type,
                            monitor_subtype, monitor_type_config, monitor_id='empty'):
        try:
            file_name = self.get_template_file_name(monitor_type, monitor_subtype)

            with open(file_name) as file:
                data = file.read()
            template_variables = {
                'region': region, 'stage': stage, 'application_name': application_name,
                'slack_notification_channel': default_configs.get('slack_notification_channel'),
                'warning_threshold': monitor_type_config.get('warning_threshold'),
                'critical_threshold': monitor_type_config.get('critical_threshold'),
                'monitor_type': monitor_type, 'monitor_subtype': monitor_subtype, 'monitor_id': monitor_id
            }
            template_rendered = data.format_map(MonitorDefault(template_variables))
            monitor_config = yaml.safe_load(template_rendered)
            return (True, (monitor_config.get('name'),
                            monitor_config.get('message'),
                            monitor_config.get('monitor_options'),
                            monitor_config.get('query'),
                            monitor_config.get('tags'),
                            monitor_config.get('type')))
        except Exception as e:
            logging.error('Cannot load file: {} because of {}'.format(file_name, e))
            return (False, str(e))

    def create_monitor(self, region, stage, application_name, default_configs,
                        monitor_type, monitor_subtype, monitor_type_config):
        logging.info(monitor_type_config, default_configs)
        monitor_config_maybe = self.render_template(region, stage, application_name,
                                                        default_configs, monitor_type,
                                                        monitor_subtype,  monitor_type_config)

        if monitor_config_maybe[0]:
            logging.info(monitor_config_maybe[1])
            datadog_api_response = self.datadog_api_monitor_create(monitor_config_maybe[1])
            if datadog_api_response[0]:
                return (True, datadog_api_response[1])
            else:
                return (False, datadog_api_response[1])
        else:
            logging.error('Rendering template was not successful for {} {}'.format(
                monitor_type, monitor_subtype))
            return (False, {'error': monitor_config_maybe[1]})

    def update_monitor(self, region, stage, application_name, default_configs,
                        monitor_type, monitor_subtype, monitor_type_config, monitor_id):
        logging.info(monitor_type_config, default_configs)
        monitor_config_maybe = self.render_template(region, stage, application_name,
                                                        default_configs, monitor_type,
                                                        monitor_subtype,  monitor_type_config)
        if monitor_config_maybe[0]:
            logging.info(monitor_config_maybe[1])
            datadog_api_response = self.datadog_api_monitor_update(monitor_config_maybe[1], monitor_id)
            if datadog_api_response[0]:
                return (True, datadog_api_response[1])
            else:
                return (False, datadog_api_response[1])
        else:
            logging.error('Rendering template was not successful for {} {}'.format(
                monitor_type, monitor_subtype))
            return (False, {'error': monitor_config_maybe[1]})

class SystemMonitors(Monitors):
    pass

class AwsElbMonitors(Monitors):
    pass

#############################################################################
################################# main ######################################
#############################################################################

def safe_load_yaml(file_name):
    try:
        with open(file_name, 'r') as file:
            data = yaml.safe_load(file)
        return (True, data)
    except Exception as e:
        logging.error('Cannot load file: {} because of {}'.format(file_name, e))
        return (False, '')

def save_application_yaml(file_name, dict):
    try:
        with open(file_name, 'w') as file:
            file.write(yaml.safe_dump(dict))
        return True
    except Exception as e:
        logging.error('Cannot write file: {} because of {}'.format(file_name, e))
        return False

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

        default_configs_location = application_config.get('default_configs_location', None)
        if default_configs_location == 'region':
            logging.info('Default configs are loaded from region.yaml')
            default_configs = region_config.get('default_configs', None)
        elif default_configs_location == 'stage':
            logging.info('Default configs are loaded from stage.yaml')
            default_configs = stage_config.get('default_configs', None)
        else:
            logging.error('Cannot find default configs. Exitting.')
            exit(1)

        for monitor_type in monitor_types_to_be_deployed:
            logging.info('{} {} {} {}'.format(args.region, args.stage, application, monitor_type))
            monitor_type_configs_location_maybe = application_config.get('{}_configs_location'.format(monitor_type), None)
            if monitor_type_configs_location_maybe:
                logging.info('Region: {} Stage: {} App: {} Type: {}  Location: {}'.format(args.region, args.stage,
                                                                                            application, monitor_type,
                                                                                            monitor_type_configs_location_maybe))
                if monitor_type_configs_location_maybe == 'region':
                    monitor_type_configs = region_config.get('{}_configs'.format(monitor_type), None)
                elif monitor_type_configs_location_maybe == 'stage':
                    monitor_type_configs = stage_config.get('{}_configs'.format(monitor_type), None)
                elif monitor_type_configs_location_maybe == 'application':
                    monitor_type_configs = application_config.get('{}_configs'.format(monitor_type), None)
                else:
                    logging.error('Monitoring config {} cannot be found'.format(monitor_type))
                    continue
            else:
                logging.error('Monitoring config {} cannot be found'.format(monitor_type))
                continue

            monitor_type_class = monitor_types.get(monitor_type, None)
            if monitor_type_class:
                cls = str_to_class(monitor_type_class)
                monitors_instance = cls(args,config)
                for monitor_subtype in monitor_type_configs:
                    monitor_type_deployed = application_config.get('{}_configs_deployed'.format(monitor_type), {}).get(monitor_subtype, None)
                    if monitor_type_deployed:
                        logging.info('Updating monitor: {}'.format(monitor_subtype))
                        monitor_id = monitor_type_deployed.get('monitor_id')
                        datadog_api_reponse = monitors_instance.update_monitor(args.region, args.stage, application,
                                                        default_configs, monitor_type, monitor_subtype,
                                                        monitor_type_configs.get(monitor_subtype), monitor_id)
                    else:
                        logging.info('Creating monitor: {}'.format(monitor_subtype))
                        datadog_api_reponse = monitors_instance.create_monitor(args.region, args.stage, application,
                                                        default_configs, monitor_type, monitor_subtype,
                                                        monitor_type_configs.get(monitor_subtype))
                    # Updating the monitor specific part of application.yaml
                    if datadog_api_reponse[0]:
                        if datadog_api_reponse[1].get('errors', False):
                            logging.error('Error happened while talking to the DataDog API')
                            logging.error(datadog_api_reponse[1].get('errors'))
                        else:
                            logging.info('Talking to the DataDog API was successful')
                            monitors_type_deployed = '{}_configs_deployed'.format(monitor_type)
                            application_config.setdefault(monitors_type_deployed,{})
                            monitor_id          = datadog_api_reponse[1].get('id', 123)
                            monitor_org_id      = datadog_api_reponse[1].get('org_id', 0)
                            monitor_creator     = datadog_api_reponse[1].get('creator', application_config.get(monitors_type_deployed, {}).get(monitor_subtype, {}).get('monitor_creator', {}))
                            monitor_created_at  = datadog_api_reponse[1].get('created', '2019-11-25T09:00:00Z')
                            monitor_updated_at  = datadog_api_reponse[1].get('modified', '2019-11-26T09:00:00Z')
                            configs_deployed    = {
                                'monitor_id': monitor_id, 'monitor_org_id': monitor_org_id,
                                'monitor_creator': monitor_creator, 'monitor_created_at': monitor_created_at,
                                'monitor_updated_at': monitor_updated_at
                            }
                            application_config[monitors_type_deployed].setdefault(monitor_subtype,configs_deployed)
                            application_config[monitors_type_deployed][monitor_subtype] = configs_deployed
                    else:
                        logging.error(datadog_api_reponse[1])
            else:
                logging.error('Cannot find class for monitor type: {}'.format(monitor_type))
            #save application.yaml
            application_yaml_saved = save_application_yaml(application_path, application_config)
            if application_yaml_saved:
                logging.info('application.yaml is successfully saved')
            else:
                logging.error('application.yaml was NOT successfully saved')

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
        logging.exception('Exception caught: %s', e)
        exit(1)
    finally:
        logging.info("Quitting...")

if __name__ == '__main__':
    exit(main())
