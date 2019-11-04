# data-cat

Deploying DataDog for a large scale infrastructure

![image](imgs/cat.svg) <3 ![image](imgs/dd.svg)

## Definitions

- Geographic Regions
- Stages
- Applications

### Geographic Regions

Matches the definitions of AWS Regions. It can be used for GCP or on-prem datacenter as well.

### Stages

Different stages of application deployments, usually: dev, qa, prod.

### Applications

A service that provides a distinct business functionality. 

## Goals

- having all monitors and dashboards in version control
- having all monitors templated 
- being able to address smaller parts of the infrastructure

## Implementation

3 files represent the DataDog configuration for the whole infrastructure.

- infrastructure.json

It contains the logical grouping of applications into stages and regions. The relations are always N:M. 1 region can contain many stages and many applications in each stage.

- defaults.json

Defaults for a certain stage.

- application.json

Configuration that is specific for a certain region, stage, application triplet.

### Generating infrastructure.json

I recently discovered [Dhall](https://dhall-lang.org) that seems like the perfect fit to write the infrastructure in and than generate the JSON files.

The type safe definitions looks like the following:

```Dhall
let keyValue =
        λ(k : Type)
      → λ(v : Type)
      → λ(mapKey : k)
      → λ(mapValue : v)
      → { mapKey = mapKey, mapValue = mapValue }

let ApplicationConfig : Type = { created_at : Text } 

let Application = < etcd | postgresql | hadoop >
let Applications = Prelude.Map.Type Application ApplicationConfig
let application = keyValue Application ApplicationConfig

let Stage = < dev | qa | prod >
let Stages = Prelude.Map.Type Stage Applications
let stage = keyValue Stage Applications

let AwsRegion = < us-east-1 | eu-central-1 | eu-west-1 >
let AwsRegions = Prelude.Map.Type AwsRegion Stages
let awsRegion = keyValue AwsRegion Stages
```

After having these definitions we can create the infrastructure:

```Dhall
in  [ awsRegion AwsRegion.us-east-1
        [ stage Stage.dev
             [ application Application.hadoop { created_at = "2019-11-04T09:00:00Z" } 
             , application Application.etcd { created_at = "2019-11-04T09:00:00Z" } 
             ]
        , stage Stage.qa
             [ application Application.hadoop { created_at = "2019-11-04T09:00:00Z" } 
             , application Application.etcd { created_at = "2019-11-04T09:00:00Z" } 
             ]
        ]
        
    , awsRegion AwsRegion.eu-west-1
        [ stage Stage.dev
             [ application Application.hadoop { created_at = "2019-11-04T09:00:00Z" } 
             , application Application.etcd { created_at = "2019-11-04T09:00:00Z" } 
             ]
        ]
    , awsRegion AwsRegion.eu-central-1
        [ stage Stage.dev
            [ application Application.hadoop { created_at = "2019-11-04T09:00:00Z" } 
            , application Application.etcd { created_at = "2019-11-04T09:00:00Z" } 
            ]
        ]
    ]
```

Generating the JSON:

```bash
dhall-to-json --file infrastructure.dhall > infrastructure.json
```

### Generating the folder structure

```Bash
python3 gen.py                                                                        
region: eu-central-1, stage: dev
region: eu-central-1, stage: dev, app: etcd
region: eu-central-1, stage: dev, app: hadoop
region: eu-west-1, stage: dev
region: eu-west-1, stage: dev, app: etcd
region: eu-west-1, stage: dev, app: hadoop
region: eu-west-1, stage: prod
region: eu-west-1, stage: prod, app: etcd
region: eu-west-1, stage: prod, app: hadoop
```

### Temlates

Templates folder has the monitor templates. 

Example template:

```YAML
---
name: High CPU load on application_name:{application_name} stage:{stage} {{{{host.name}}}} / {{{{host.ip}}}}
tags:
  - application_name:{application_name}
  - stage:{stage}
  - region:{region}
type: metric alert
query: avg(last_5m):avg:system.load.norm.5{{application_name:{application_name},stage:{stage}}} by {{host}} > {critical_threshold}
message: >-2
  High CPU load on application_name:{application_name} stage:{stage} {{{{host.name}}}} / {{{{host.ip}}}} for 5 consecutive minutes on this node.
  Url: https://wd-global-prod.datadoghq.com/monitors/{monitor_id}
  {slack_notification_channel}
monitor_options:
  notify_audit: False
  locked: False
  timeout_h: 0
  silenced: {{}}
  include_tags: True
  require_full_window: True
  new_host_delay: 300
  notify_no_data: False
  renotify_interval: 0
  escalation_message: >-2
    CPU load is still damn high.
  thresholds:
    critical: {critical_threshold}
    warning: {warning_threshold}
```

This gets rendered using Python format and converted to a dict that used to talk to the DataDog API.

### Defaults and specifics

Defaults are stage wide settings specifics are specific to a single application (in a region & stage).

### Tags alignment

For all of these above to work together nicely there is a dependency on tags being deployed every node, ELB, etc., so that we can reference those in monitors and dashboards.

## Deployment

I gave up on Conda and now just using venv from Python.

```Bash
/usr/local/opt/python3/bin/python3 -m venv venv
. venv/bin/activate.fish #or the shell you are using
pip install --upgrade pip
pip install --upgrade toml pyyaml
```

### Deploying monitors

Deploying a whole stage:

```bash
./data-cat/data-cat.py deploy-monitors -r eu-west-1 -s qa 
```

Deploying a single application:

```bash
./data-cat/data-cat.py deploy-monitors -r eu-west-1 -s qa -a etcd
```

### Deploying dashboards

Deploying a whole stage:

```bash
./data-cat/data-cat.py deploy-dashboards -r eu-west-1 -s qa 
```

Deploying a single application:

```bash
./data-cat/data-cat.py deploy-dashboards -r eu-west-1 -s qa -a etcd
```

## About Us

LambdaInsight is a consultancy located in Europe working on large scale infrastructures mostly in the intersection of data and cloud.

Let us know if you are interested in a project with us.

