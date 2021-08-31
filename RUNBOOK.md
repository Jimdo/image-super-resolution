# Image Super Resolution - Sharp Worker

This worker reads from and publish to kafka. It wraps the image-super-resolution libraries with a kafka consumer and a kafka producer.
The source topic is `KAFKA_TOPIC_USER_IMAGE_TO_PROCESS`. The destination topic is `KAFKA_TOPIC_USER_IMAGE_PROCESSED`. 
And the processed images are uploaded to the bucket specified in `PROCESSED_IMAGES_BUCKET`.
Those values are configured in the [local.docker-compose.yml](./local.docker-compose.yml) and in the
[wonderland.yaml](./wonderland.yaml) files.

## Infrastructure
This worker creates 2 buckets: 
- prod-bucket = "jimdo-sharp-processed-images-prod"
- stage-bucket = "jimdo-sharp-processed-images-stage"

It also creates a role to access those buckets. The role is then added to an *aws_config.txt* file that is placed
in the docker image. That role is used only when the service is deployed. Locally you need to have your aws credentials
configured. Check the [local.Makefile](./local.Makefile) file for more info.
The role assumes a mirror role from wonderland.

Those are created using terraform. Check the [infra.Makefile](./infra.Makefile) file for more info. 

## Running it locally
1. Start the dependencies by running
```shell script
$ make run-kafka-dependencies 
```

2. In another terminal run the docker image as
```shell script
$ make run-kafka-local
```

## Deploying it manually

### Pre-requisites
To deploy it you need to make sure about 3 things:
1. You don't have any changes. That means, your commit is clean. 
Use `$ make print-image-tag` to check if your commit is *dirty*.
2. You need to create an *aws_config* file. Otherwise, your *build* step will fail.
To create that file just run `$ make create-aws-config`.
3. You need to run `$ make build-and-push` to push the docker image.

### Deploying
Just run `$ ENV=stage make deploy` or `$ ENV=prod make deploy`
