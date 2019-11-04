let keyValue =
        λ(k : Type)
      → λ(v : Type)
      → λ(mapKey : k)
      → λ(mapValue : v)
      → { mapKey = mapKey, mapValue = mapValue }

let Prelude = https://prelude.dhall-lang.org/v11.1.0/package.dhall

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
        , stage Stage.qa
             [ application Application.hadoop { created_at = "2019-11-04T09:00:00Z" } 
             , application Application.etcd { created_at = "2019-11-04T09:00:00Z" } 
             ]
        , stage Stage.prod
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

