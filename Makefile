build-server: Dockerfile.service.cpu
	docker build -t serve-isr . -f Dockerfile.service.cpu
#	docker tag serve-isr registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution

gpu-build:
	docker build -t serve-isr-gpu . -f Dockerfile.service.gpu
	docker tag serve-isr-gpu registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution-gpu2

gpu-push:
	wl docker push registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution-gpu

gpu-run:
	nvidia-docker run --rm --gpus all -e PORT=80 -p 80:80 -it serve-isr-gpu
	#docker run --rm --gpus all -e PORT=80 -p 80:80 -it serve-isr-gpu

push:
	wl docker push registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution

deploy:
	wl service deploy --watch op-image-super-resolution

service-delete:
	wl service delete op-image-super-resolution

run:
	docker run -v $(pwd)/data/:/home/isr/data -v $(pwd)/weights/:/home/isr/weights -v $(pwd)/config.yml:/home/isr/config.yml -it isr -p -d -c config.yml

serve:
	docker run -e PORT=3000 -p 3000:3000 -it serve-isr

logs:
	wl logs op-image-super-resolution -f

ping:
	curl https://op-image-super-resolution.jimdo-platform.net/
