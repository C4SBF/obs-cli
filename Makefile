.PHONY: build run scan discover classify clean help

OUTPUT_DIR ?= ./data

help:
	@echo "obs-cli - BACnet network discovery tool"
	@echo ""
	@echo "Usage:"
	@echo "  make build              Build Docker image"
	@echo "  make scan [network]     Quick network scan (default: host)"
	@echo "  make discover [network] Full discovery (default: host)"
	@echo "  make clean              Remove output data"
	@echo ""
	@echo "Examples:"
	@echo "  make discover"
	@echo "  make discover bacnet_net"
	@echo "  make scan host"

build:
	docker build -t obs-cli .

run:
	docker run --rm --network $(or $(filter-out $@,$(MAKECMDGOALS)),host) \
		-v $(OUTPUT_DIR):/data obs-cli $(ARGS)

scan:
	@mkdir -p $(OUTPUT_DIR)
	docker run --rm --network $(or $(filter-out $@,$(MAKECMDGOALS)),host) \
		-v $(OUTPUT_DIR):/data obs-cli scan --output /data/devices.yaml
	@echo "Results: $(OUTPUT_DIR)/devices.yaml"

discover:
	@mkdir -p $(OUTPUT_DIR)
	docker run --rm --network $(or $(filter-out $@,$(MAKECMDGOALS)),host) \
		-v $(OUTPUT_DIR):/data obs-cli discover --output /data/discovery.yaml
	@echo "Results: $(OUTPUT_DIR)/discovery.yaml"

classify:
	docker run --rm -v $(OUTPUT_DIR):/data obs-cli \
		classify --input /data/discovery.yaml --output /data/classified.yaml
	@echo "Results: $(OUTPUT_DIR)/classified.yaml"

clean:
	rm -rf $(OUTPUT_DIR)/*.yaml $(OUTPUT_DIR)/*.json

# Catch-all to allow positional args
%:
	@:
