VERSION = 7f7de49 #$(shell git rev-parse --short HEAD)
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
	PROJECT_NAME=$(PROJECT_NAME) \
	COMPONENT_NAME=$(COMPONENT_NAME) \
	envsubst < wonderland2.template.yaml > wonderland2.yaml

wl2.status: wl
	wl kubectl get deploy $(PROJECT_NAME)

wl2.pods: wl
	wl kubectl get pods | grep $(PROJECT_NAME)

wl2.describe: wl
	wl kubectl describe pod $(PROJECT_NAME) > /tmp/runbooks_describe_pod_$(PROJECT_NAME).txt && less /tmp/runbooks_describe_pod_$(PROJECT_NAME).txt

wl2.deploy: wl guard-JIMDO_ENVIRONMENT wl2.gen
	wl kubectl apply -f wonderland2.yaml

wl2.test-image:
	curl $(PROJECT_NAME)-prod.jimdo-platform-eks.net/magnify?by_patch_of_size=30&padding_size=13&batch_size=5&image_url=https%3A%2F%2Fjimdo-storage.freetls.fastly.net%2Fimage%2F188163642%2Fdda9a2c3-f1a1-49e8-a773-d66051733cd9.jpg -o img.jpg

guard-%:
	@ if [ "${${*}}" = "" ]; then \
	    echo "Environment variable $* not set"; \
	    exit 1; \
	fi
