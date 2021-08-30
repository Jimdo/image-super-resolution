include local.Makefile
include infra.Makefile

SERVICE_NAME								= sharp-worker-isr-processor
REGISTRY                                    = registry.jimdo-platform.net
IMAGE                                       = $(REGISTRY)/jimdo/sharp/$(SERVICE_NAME)
TAG                                     	= $(shell git describe --always --dirty)
IMAGE_TAG                                  	= $(IMAGE):$(TAG)
WL                                          = ./wl
VERSION                                     = $(TAG)

export TAG
export ENV
export VERSION
export IMAGE_TAG
export SERVICE_NAME

guard-%:
	@ if [ "${${*}}" = "" ]; then \
	    echo "Environment variable $* not set"; \
	    exit 1; \
	fi

wl:
	curl -sSLfo $(WL) https://downloads.jimdo-platform.net/wl/latest/wl_latest_$(shell uname -s | tr A-Z a-z)_$(shell uname -m | sed "s/x86_64/amd64/")
	chmod +x $(WL)

build: Dockerfile.kafka.cpu
	docker build -t $(IMAGE_TAG) . -f Dockerfile.kafka.cpu

pull: wl
	$(WL) docker pull $(IMAGE_TAG)

push: wl
	$(WL) docker push $(IMAGE_TAG)

build-and-push: build push

deploy: $(WL) guard-ENV
	$(WL) deploy $(SERVICE_NAME)-$(ENV) -f ./wonderland.yaml

.PHONY: build test push pull deploy build-and-push
