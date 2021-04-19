proxy-build:
	docker build -t isr-proxy -f ./nginx/Dockerfile ./nginx
	docker tag isr-proxy registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution-proxy

proxy-push:
	wl docker push registry.jimdo-platform.net/jimdo/jonathanmv/op/image-super-resolution-proxy

proxy-deploy:
	wl service deploy --watch op-image-super-resolution-proxy

build-server: Dockerfile.service.cpu
	docker build -t serve-isr . -f Dockerfile.service.cpu

run:
	docker run -v $(pwd)/data/:/home/isr/data -v $(pwd)/weights/:/home/isr/weights -v $(pwd)/config.yml:/home/isr/config.yml -it isr -p -d -c config.yml

serve:
	docker run -e PORT=3000 -p 3000:3000 -it serve-isr

logs:
	wl logs op-image-super-resolution -f

ping:
	curl https://op-image-super-resolution.jimdo-platform.net/
