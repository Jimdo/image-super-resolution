# Image Super Resolution - Sharp Worker

This worker reads from and publishes to kafka. It wraps the [image-super-resolution](https://github.com/idealo/image-super-resolution)
libraries with a kafka consumer and a kafka producer.
The source topic is `KAFKA_TOPIC_USER_IMAGE_TO_PROCESS`. The destination topic is `KAFKA_TOPIC_USER_IMAGE_PROCESSED`. 
And the processed images are uploaded to the bucket specified in `PROCESSED_IMAGES_BUCKET`.
Those values are configured in the [local.docker-compose.yml](./local.docker-compose.yml) and in the
[wonderland.yaml](./wonderland.yaml) files.

The consumed message schema is specified in the [user-image-uploaded-event.avro](./ISR/avro/user-image-uploaded.avro).
The produced message schema is specified in the [image-super-resolution-processed-image.avro](./ISR/avro/image-super-resolution-processed-image.avro).


## How it works

After the worker starts, it polls messages from `KAFKA_TOPIC_USER_IMAGE_TO_PROCESS`. 
When a new message is available, it downloads the image specified in the `url` attribute.
It processes the image with the configured params:
 - model_name
 - by_patch_of_size
 - batch_size
 - padding_size
 
 It saves the result locally before uploading it to the `PROCESSED_IMAGES_BUCKET` in S3.
 Finally, it creates a message in the `KAFKA_TOPIC_USER_IMAGE_PROCESSED` topic with the structure of the 
 [image-super-resolution-processed-image.avro](./ISR/avro/image-super-resolution-processed-image.avro) schema.

## Running it locally

1. Start the dependencies by running
```shell script
$ make run-kafka-dependencies 
```

2. In another terminal run the docker image as
```shell script
$ make run-kafka-local
```
This will produce records to the source topic and start the kafka worker.
If you need to produce more records while the worker is running, just execute:
```shell script
$ make produce-records
```
This will publish the records in the [user-image-uploaded-records.json](./scripts/user-image-uploaded-records.json)
to the source topic. You can add/remove records from the file. Make sure to follow the structure.

There's also a command to run the container and have the *bash* as the entry point.
```shell script
$ make run-kafka-local-bash
```


## Evolving the schema

The schema registry has the `BACKWARD` compatibility option enabled by default. So if you make changes to the schemas 
they need to be compatible with old schemas. For example, when adding a new field, make sure to set a `default` value. 

Schemas are applied automatically when a new record is processed and is about to be send to the `KAFKA_TOPIC_USER_IMAGE_PROCESSED` topic.
If the schema is not compatible, you will get an error similar to:

```shell script
confluent_kafka.schema_registry.error.SchemaRegistryError:
Schema being registered is incompatible with an earlier schema for subject "sharp-processed-images-value"
```

### Interacting with the schema registry

The schema registry for prod is hosted at https://schema-registry-engineering-prod.jimdo-platform.net, however you can't 
make requests directly to it. You can use ssh tunnelling like this:

- Open a ssh tunnel in one terminal:
```shell script
$ ssh -i ~/.ssh/id_rsa.pem \
    jonathanmv@infra.bastion.prod.aws.jimdo-server.com -p2022 \
    -L 8088:schema-registry-engineering-prod.jimdo-platform.net:443 \
    -N
```

This creates a connection between the local port `8088` and the remote port `443`.

- In another terminal run your schema registry request:
```shell script
$ curl -k https://localhost:8088/schemas/ids/2
``` 

Check more Schema Registry API examples [here](https://docs.confluent.io/platform/current/schema-registry/develop/using.html)

## Infrastructure

This worker creates 2 buckets:
- prod-bucket = "jimdo-sharp-processed-images-prod"
- stage-bucket = "jimdo-sharp-processed-images-stage"

It also creates a role to access those buckets. The role is then added to an *aws_config.txt* file that is copied inside the
 docker image, under *~/.aws/config*. That role is used only when the service is deployed. Locally you need to have your aws credentials
configured. Check the [local.Makefile](./local.Makefile) file for more info.

The role assumes a mirror role from wonderland. You can check the assumed role in the [wonderland.yaml](./wonderland.yaml) file.

The resources are created using terraform. Check the [infra.Makefile](./infra.Makefile) file for more info.


## Deploying it manually

### Pre-requisites

To deploy it you need to do 3 things:
1. Commit all your changes. Use `$ make print-image-tag` to check if your commit is *dirty*.
2. Create an *aws_config* file. Otherwise, your *build* step will fail.
To create that file just run `$ make create-aws-config`.
This will apply the infrastructure and create the file with as part of the outputs.
3. Build and push the docker image using `$ make build-and-push`.


### Deploying

Just run `$ ENV=stage make deploy` or `$ ENV=prod make deploy`


### Monitoring

Production:
- [Logs](https://app-eu.logz.io/#/goto/14ac651e4e5f47c1e31e28aad112061f?switchToAccountId=15295)
- [Grafana](https://grafana.jimdo-platform.net/d/000000122/wonderland-user-services?orgId=1&refresh=1m&var-collector=prometheus.jimdo-platform.net&var-service=sharp-worker-isr-processor-prod&var-component=All&from=now-3h&to=now)
- [Source messages](https://kafka-akhq-engineering.jimdo-platform.net/ui/prod/topic/sharp-images-to-process/data?sort=Newest&partition=All)
- [Processed messages](https://kafka-akhq-engineering.jimdo-platform.net/ui/prod/topic/sharp-processed-images/data?sort=Newest&partition=All)
- [Bucket](https://s3.console.aws.amazon.com/s3/buckets/jimdo-sharp-processed-images-prod?region=eu-west-1&tab=objects)

Staging:
- [Logs](https://app-eu.logz.io/#/goto/2f98829399ee1b6775f57311eb77141b?switchToAccountId=15295)
- [Grafana](https://grafana.jimdo-platform.net/d/000000122/wonderland-user-services?orgId=1&refresh=1m&var-collector=prometheus.jimdo-platform.net&var-service=sharp-worker-isr-processor-stage&var-component=All&from=now-3h&to=now)
- [Source messages](https://kafka-akhq-engineering.jimdo-platform.net/ui/stage/topic/sharp-images-to-process/data?sort=Newest&partition=All)
- [Processed messages](https://kafka-akhq-engineering.jimdo-platform.net/ui/stage/topic/sharp-processed-images/data?sort=Newest&partition=All)
- [Bucket](https://s3.console.aws.amazon.com/s3/buckets/jimdo-sharp-processed-images-stage?region=eu-west-1&tab=objects)
