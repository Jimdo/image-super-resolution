build-kafka: Dockerfile.kafka.cpu
	docker build -t kafka-isr . -f Dockerfile.kafka.cpu

run-kafka-local: build-kafka
	docker-compose -f kafka.docker-compose.yml \
		-f local.docker-compose.yml \
		run -e AWS_SECRET_ACCESS_KEY -e AWS_ACCESS_KEY_ID --rm kafka-sharp-worker

run-kafka-dependencies: stop-kafka-dependencies
	docker-compose -f kafka.docker-compose.yml up

stop-kafka-dependencies:
	docker-compose -f kafka.docker-compose.yml down

run:
	docker run -v $(pwd)/data/:/home/isr/data -v $(pwd)/weights/:/home/isr/weights -v $(pwd)/config.yml:/home/isr/config.yml -it isr -p -d -c config.yml

produce-records:
	docker-compose -f kafka.docker-compose.yml exec -T schema-registry \
		kafka-avro-console-producer \
		  --topic dev-sharp-images-to-process \
		  --bootstrap-server broker:29092 \
		  --property value.schema="$$(< ISR/avro/user-image-uploaded.avro)" \
		  < ./scripts/user-image-uploaded-records.json
