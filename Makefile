proxy-build:
	docker build -t isr-proxy -f ./nginx/Dockerfile ./nginx
	docker tag isr-proxy registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution-proxy

proxy-push:
	wl docker push registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution-proxy

proxy-deploy:
	wl service deploy --watch op-image-super-resolution-proxy

proxy-delete:
	wl service delete op-image-super-resolution-proxy

build-server: Dockerfile.service.cpu
	docker build -t serve-isr . -f Dockerfile.service.cpu

build-kafka: Dockerfile.kafka.cpu
	docker build -t kafka-isr . -f Dockerfile.kafka.cpu

run-kafka-docker:
	docker run \
		-e KAFKA_BOOTSTRAP_SERVERS=broker:9092 \
		-e KAFKA_GROUP_ID=ist-kafka-consumer \
		-e KAFKA_AUTO_OFFSET_RESET=earliest \
		-e KAFKA_ENABLE_AUTO_COMMIT=0 \
		-e MODEL_NAME=noise-cancel \
		-e MODEL_BY_PATCH_OF_SIZE=30 \
		-e MODEL_BATCH_SIZE=13 \
		-e MODEL_PADDING_SIZE=5 \
		-e KAFKA_TOPICS=user-image-uploaded \
		--rm -it kafka-isr

run-kafka-local: build-kafka
	docker-compose -f kafka.docker-compose.yml \
		-f local.docker-compose.yml \
		run --rm kafka-sharp-worker

run-kafka-dependencies: stop-kafka-dependencies
	docker-compose -f kafka.docker-compose.yml up

stop-kafka-dependencies:
	docker-compose -f kafka.docker-compose.yml down

run:
	docker run -v $(pwd)/data/:/home/isr/data -v $(pwd)/weights/:/home/isr/weights -v $(pwd)/config.yml:/home/isr/config.yml -it isr -p -d -c config.yml

serve:
	docker run -e PORT=3000 -p 3000:3000 -it serve-isr

serve-with-restrictions:
	docker run -e PORT=3000 -p 3000:3000 -m 1g --cpus=".5" -it serve-isr

logs:
	wl logs op-image-super-resolution -f

ping:
	curl https://op-image-super-resolution.jimdo-platform.net/
