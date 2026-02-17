# obs-cli

CLI tool for BACnet network discovery using [obs-python](https://github.com/C4SBF/obs-python).

## Features

- **Network Scan**: Discover BACnet devices on a network
- **Full Discovery**: Scan network and read all device objects/points
- **YAML/JSON Output**: Export results in structured formats

## Usage

### Using pre-built image

```bash
docker pull ghcr.io/c4sbf/obs-cli:latest
```

### Building locally

```bash
make build
```

### Network Scan (Census)

Quick scan to discover devices:

```bash
make scan                # uses host network
make scan bacnet_net     # uses docker network
```

### Full Discovery

Scan network and read all objects from each device:

```bash
make discover            # uses host network
make discover bacnet_net # uses docker network
```

### Direct Docker Usage

```bash
docker run --rm --network host -v $(pwd)/data:/data ghcr.io/c4sbf/obs-cli:latest \
  discover --output /data/discovery.yaml
```

With specific network CIDR:

```bash
docker run --rm --network bacnet_net -v $(pwd)/data:/data ghcr.io/c4sbf/obs-cli:latest \
  discover --network 172.20.0.0/16 --output /data/discovery.yaml
```

## Output Format

Results are output as YAML (default) or JSON:

```yaml
nodes:
  - id: "bacnet://192.168.1.10/1001"
    type: device
    attrs:
      name: "AHU-1"
      manufacturer: "Vendor"

  - id: "bacnet://192.168.1.10/1001/analogInput:1"
    type: point
    attrs:
      name: "Supply Air Temp"
      unit: "degF"
      data_type: float

edges:
  - source: "bacnet://192.168.1.10/1001"
    target: "bacnet://192.168.1.10/1001/analogInput:1"
    type: hasPoint

meta:
  success: true
```

## License

Apache-2.0
