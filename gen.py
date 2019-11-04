#!/usr/bin/env python
import yaml
import os, sys

with open('infrastructure.yaml', 'r') as read_file: infra = yaml.load(read_file, Loader=yaml.FullLoader)

regions = infra.keys()
for region in regions:
    stages = infra[region].keys()
    for stage in stages:
      print('region: {}, stage: {}'.format(region, stage))
      stage_folder = os.path.join('infra', region, stage)
      os.makedirs(stage_folder, 0o750, exist_ok=True)
      with open(os.path.join(stage_folder, 'application.yaml'), 'a'): pass
      apps = infra[region][stage].keys()
      for app in apps:
        print('region: {}, stage: {}, app: {}'.format(region, stage, app))
        app_folder = os.path.join('infra', region, stage, app)
        os.makedirs(app_folder, 0o750, exist_ok=True)
        with open(os.path.join(app_folder, 'application.yaml'), 'a'): pass
            


