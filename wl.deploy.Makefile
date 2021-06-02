VERSION = $(shell git rev-parse --short HEAD)
TAG = $(VERSION)
REGISTRY = registry.jimdo-platform.net
PROJECT_NAME = sharp-isr-server
IMAGE = $(REGISTRY)/jimdo/sharp/$(PROJECT_NAME)
COMPONENT_NAME = $(PROJECT_NAME)-$(JIMDO_ENVIRONMENT)

NAMESPACE = sharp-stage
ifeq ($(JIMDO_ENVIRONMENT),prod)
	NAMESPACE = sharp
endif

wl:
	curl -sSLfo ./wl https://downloads.jimdo-platform.net/wl/latest/wl_latest_$(shell uname -s | tr A-Z a-z)_$(shell uname -m | sed "s/x86_64/amd64/")
	chmod +x ./wl

.PHONY: wl2.build
wl2.build:
	docker build -t $(IMAGE):$(TAG) . -f Dockerfile.service.cpu

.PHONY: wl2.push
wl2.push: wl wl2.build
	./wl docker push $(IMAGE):$(TAG)

.PHONY: wl2.gen
wl2.gen: guard-JIMDO_ENVIRONMENT
	NAMESPACE=$(NAMESPACE) \
	IMAGE=$(IMAGE) \
	VERSION=$(VERSION) \
	TAG=$(TAG) \
	JIMDO_ENVIRONMENT=$(JIMDO_ENVIRONMENT) \
	COMPONENT_NAME=$(COMPONENT_NAME) \
	envsubst < wonderland2.template.yaml > wonderland2.yaml

wl2.status: wl
	wl kubectl get ws -n sharp

wl2.deploy: wl guard-JIMDO_ENVIRONMENT wl2.gen
	wl kubectl apply -f wonderland2.yaml

guard-%:
	@ if [ "${${*}}" = "" ]; then \
	    echo "Environment variable $* not set"; \
	    exit 1; \
	fi
