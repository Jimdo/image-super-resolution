build-kafka: Dockerfile.kafka.cpu
	docker build -t kafka-isr . -f Dockerfile.kafka.cpu

run-kafka-local: build-kafka
	make produce-records
	docker-compose -f kafka.docker-compose.yml \
		-f local.docker-compose.yml \
		run -e AWS_SECRET_ACCESS_KEY -e AWS_ACCESS_KEY_ID --rm kafka-sharp-worker

run-kafka-local-bash: build-kafka
	docker run \
		-e "KAFKA_SCHEMA_REGISTRY_URL=http://schema-registry:8081" \
	    -e "KAFKA_BOOTSTRAP_SERVERS=broker:9092" \
	    -e "KAFKA_CONSUMER_GROUP_ID=ist-kafka-consumer" \
	    -e "KAFKA_CONSUMER_AUTO_OFFSET_RESET=earliest" \
	    -e "KAFKA_CONSUMER_ENABLE_AUTO_COMMIT=0" \
	    -e "KAFKA_CONSUMER_POLLING_TIMEOUT_SECONDS=30" \
	    -e "KAFKA_CONSUMER_MAX_POLL_INTERVAL_MS=3000000" \
	    -e "MODEL_NAME=noise-cancel" \
	    -e "MODEL_BY_PATCH_OF_SIZE=30" \
	    -e "MODEL_BATCH_SIZE=13" \
	    -e "MODEL_PADDING_SIZE=13" \
	    -e "KAFKA_TOPIC_USER_IMAGE_TO_PROCESS=dev-sharp-images-to-process" \
	    -e "KAFKA_TOPIC_USER_IMAGE_PROCESSED=dev-sharp-processed-images" \
	    -e "PROCESSED_IMAGES_BUCKET=jimdo-sharp-processed-images-stage" \
		-v data:/home/isr/data \
		--network="image-super-resolution-jimdo_default" \
		--entrypoint /bin/bash \
		--rm -it kafka-isr

run-kafka-dependencies: stop-kafka-dependencies
	docker-compose -f kafka.docker-compose.yml up

stop-kafka-dependencies:
	docker-compose -f kafka.docker-compose.yml down

produce-records:
	docker-compose -f kafka.docker-compose.yml exec -T schema-registry \
		kafka-avro-console-producer \
		  --topic dev-sharp-images-to-process \
		  --bootstrap-server broker:29092 \
		  --property value.schema="$$(< ISR/avro/user-image-uploaded.avro)" \
		  < ./scripts/user-image-uploaded-records.json
