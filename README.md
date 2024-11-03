# Schneider ZigBee Gateway API

Unofficial REST API for legacy Schneider U30IPGWZB ZigBee/IP Gateway, enabling smart home control for discontinued devices. Built with FastAPI, supporting dimmers, switches, and AC units.

## Overview

This project provides a modern REST API interface for the [Schneider U30IPGWZB ZigBee/IP Gateway](https://www.se.com/th/en/product/U30IPGWZB/zb-ip-gateway-rj45-wifi/). While this gateway device has been discontinued by Schneider Electric, many users still rely on it for their smart home automation. This API enables continued use and integration with modern home automation systems.

### Supported Devices
- Dimmers (brightness control)
- Switches (on/off control)
- AC Units (power, mode, temperature control)

## Prerequisites

- Python 3.8 or higher
- Schneider U30IPGWZB Gateway device
- Network access to the gateway
- Gateway credentials (username/password)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/schneider-zigbee-gateway-api.git
cd schneider-zigbee-gateway-api
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a configuration file (`config.yaml`):
```yaml
gateway_ip: "192.168.1.xxx"
username: "your_username"
password: "your_password"
devices:
  living_room_light:
    type: "DIMMER"
    entity: "0x1234"
    location: "Living Room"
  bedroom_switch:
    type: "SWITCH"
    entity: "0x5678"
    location: "Bedroom"
  living_room_ac:
    type: "AC"
    entity: "0x9012"
    location: "Living Room"
    ir_codes:
      power_on: [...]  # IR codes specific to your AC
      power_off: [...]
      cool_mode: [...]
      heat_mode: [...]
      temp_16: [...]
      # Add more temperature codes as needed
```

## Usage

1. Start the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### Get All Devices
```http
GET /devices
```

#### Get Device Status
```http
GET /device_status/{device_name}
```

#### Control Device
```http
POST /control_device
```
Request body:
```json
{
  "device_name": "living_room_light",
  "action": "on",
  "level": 80,  // Optional, for dimmers
  "ac_mode": "cool",  // Optional, for AC units
  "temperature": 24  // Optional, for AC units
}
```

### Example Requests

#### Turn on a light
```bash
curl -X POST http://localhost:8000/control_device \
  -H "Content-Type: application/json" \
  -d '{"device_name": "living_room_light", "action": "on"}'
```

#### Set dimmer level
```bash
curl -X POST http://localhost:8000/control_device \
  -H "Content-Type: application/json" \
  -d '{"device_name": "living_room_light", "action": "dim", "level": 50}'
```

#### Control AC
```bash
curl -X POST http://localhost:8000/control_device \
  -H "Content-Type: application/json" \
  -d '{"device_name": "living_room_ac", "action": "set_mode", "ac_mode": "cool", "temperature": 24}'
```

## Configuration

### Device Types
- `DIMMER`: Supports on/off and brightness level control
- `SWITCH`: Supports on/off control
- `AC`: Supports power, mode, and temperature control

### Finding Entity IDs
Entity IDs are unique identifiers for each device connected to your gateway. You can find them by:
1. Accessing your gateway's web interface
2. Looking at the device list
3. Noting down the entity ID (usually in hexadecimal format)

## Disclaimer

This is an unofficial project and is not affiliated with, endorsed by, or connected to Schneider Electric in any way. Use at your own risk.
