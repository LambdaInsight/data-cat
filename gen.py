#!/usr/bin/env python
import json
import os, sys

with open('infrastructure.json', 'r') as read_file: infra = json.load(read_file)

regions = infra.keys()
for region in regions:
    stages = infra[region].keys()
    for stage in stages:
        apps = infra[region][stage].keys()
        for app in apps:
            print('region: {}, stage: {}, app: {}'.format(region, stage, app))
            folder = os.path.join('infra', region, stage, app)
            os.makedirs(folder, 0o750, exist_ok=True)
            with open(os.path.join(folder, 'application.json'), 'a'): pass
            


