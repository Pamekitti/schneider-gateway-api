from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import time
import base64
from typing import Dict, Any, Optional
import yaml

app = FastAPI(
    title="Schneider Gateway API",
    description="API for controlling and monitoring Schneider Gateway devices",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Add your React app's URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DeviceControl(BaseModel):
    device_name: str
    action: str
    level: Optional[int] = None
    ac_mode: Optional[str] = None
    temperature: Optional[int] = None

@app.post("/control_device")
async def control_device(device_control: DeviceControl):
    try:
        result = backend.control_device(
            device_control.device_name, 
            device_control.action, 
            device_control.level,
            device_control.ac_mode,
            device_control.temperature
        )
        return {"status": "success", "result": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/device_status/{device_name}")
async def get_device_status(device_name: str):
    try:
        result = backend.read_device_status(device_name)
        return {"status": "success", "result": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
async def get_devices():
    return {"devices": [
        {
            "name": name,
            "location": device["location"],
            "type": device["type"]
        } for name, device in backend.config['devices'].items()
    ]}

class SchneiderGatewayBackend:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self.load_config()
        self.base_url = f"http://{self.config['gateway_ip']}"
        self.cookie = self.config.get('cookie', '')
        self.username = self.config['username']
        self.password = self.config['password']

    def load_config(self) -> Dict[str, Any]:
        with open(self.config_file, 'r') as file:
            return yaml.safe_load(file)

    def save_config(self):
        with open(self.config_file, 'w') as file:
            yaml.dump(self.config, file)

    def get_auth_header(self):
        auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return f"Basic {auth}"

    def is_cookie_valid(self) -> bool:
        url = f"{self.base_url}/home.html"
        headers = {
            'Cookie': f'user_id={self.cookie}',
            'Authorization': self.get_auth_header()
        }
        response = requests.get(url, headers=headers)
        return response.status_code == 200

    def login(self):
        url = f"{self.base_url}/cgi-bin/admin"
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.cookie = response.cookies.get('user_id', '')
            self.config['cookie'] = self.cookie
            self.save_config()
            print("Login successful")
        else:
            print("Login failed")
            raise HTTPException(status_code=401, detail="Login failed")
    
    def control_device(self, device_name: str, action: str, level: Optional[int] = None, ac_mode: Optional[str] = None, temperature: Optional[int] = None):
        if not self.is_cookie_valid():
            self.login()

        device_config = self.config['devices'].get(device_name)
        if not device_config:
            raise HTTPException(status_code=404, detail=f"Device {device_name} not found in configuration")

        url = f"{self.base_url}/cgi-bin/rpc_bridge"
        
        if device_config['type'] == 'DIMMER':
            if action == 'on':
                method = "RPC_ZCL_Set_OnOffTog"
                params = {"entity": device_config['entity'], "action": 1}
            elif action == 'off':
                method = "RPC_ZCL_Set_OnOffTog"
                params = {"entity": device_config['entity'], "action": 0}
            elif action == 'dim':
                if level is None:
                    raise HTTPException(status_code=400, detail="Level is required for dimming")
                method = "RPC_ZCL_Move_To"
                params = {"entity": device_config['entity'], "level": level, "transTime": 0}
            else:
                raise HTTPException(status_code=400, detail="Invalid action for DIMMER")
        elif device_config['type'] == 'SWITCH':
            if action not in ['on', 'off']:
                raise HTTPException(status_code=400, detail="Invalid action for SWITCH")
            method = "RPC_ZCL_Set_OnOffTog"
            params = {"entity": device_config['entity'], "action": 1 if action == 'on' else 0}
        elif device_config['type'] == 'AC':
            method = "RPC_ZCL_Send_IR_Code"
            ir_code = []
            if action == 'on':
                ir_code = device_config['ir_codes']['power_on']
            elif action == 'off':
                ir_code = device_config['ir_codes']['power_off']
            elif action == 'set_mode':
                if ac_mode == 'cool':
                    ir_code = device_config['ir_codes']['cool_mode']
                elif ac_mode == 'heat':
                    ir_code = device_config['ir_codes']['heat_mode']
                # Add more modes as needed
            elif action == 'set_temperature':
                if temperature is not None:
                    ir_code = device_config['ir_codes'].get(f'temp_{temperature}', [])
            
            params = {
                "entity": device_config['entity'],
                "index": 1,
                "repeat": 0,
                "codeType": 0,
                "irCode": ir_code
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported device type")

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "transId": int(time.time())
        }
        
        headers = {
            'Cookie': f'user_id={self.cookie}',
            'Content-Type': 'application/json',
            'Authorization': self.get_auth_header()
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Device control failed")
        return response.json()

    def read_device_status(self, device_name: str):
        if not self.is_cookie_valid():
            self.login()

        device_config = self.config['devices'].get(device_name)
        if not device_config:
            raise HTTPException(status_code=404, detail=f"Device {device_name} not found in configuration")

        url = f"{self.base_url}/cgi-bin/rpc_bridge"
        
        if device_config['type'] == 'DIMMER':
            methods = ["RPC_ZCL_Get_OnOff", "RPC_ZCL_Get_Level"]
        elif device_config['type'] == 'SWITCH':
            methods = ["RPC_ZCL_Get_OnOff"]
        else:
            raise HTTPException(status_code=400, detail="Unsupported device type")

        results = {}
        for method in methods:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": {"entity": device_config['entity']},
                "transId": int(time.time())
            }
            
            headers = {
                'Cookie': f'user_id={self.cookie}',
                'Content-Type': 'application/json',
                **self.get_auth_header()
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Device status read failed")
            results[method] = response.json()

        return results

backend = SchneiderGatewayBackend('config.yaml')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)