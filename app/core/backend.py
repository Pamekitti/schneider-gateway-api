import requests
import base64
import time
import logging
from typing import Dict, Any, Optional, List
from fastapi import HTTPException

from app.core.config import load_config, save_config

logger = logging.getLogger(__name__)

class SchneiderGatewayBackend:
    """Backend for interacting with Schneider Gateway devices."""
    
    def __init__(self, config_file: str):
        """Initialize the backend with configuration file.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = load_config()
        self.base_url = f"http://{self.config['gateway_ip']}"
        self.cookie = self.config.get('cookie', '')
        self.username = self.config['username']
        self.password = self.config['password']
        logger.info(f"Backend initialized with gateway at {self.base_url}")

    def get_auth_header(self) -> Dict[str, str]:
        """Generate authentication header for API requests.
        
        Returns:
            Dict containing the Authorization header
        """
        auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {auth}"}

    def is_cookie_valid(self) -> bool:
        """Check if the current session cookie is valid.
        
        Returns:
            True if cookie is valid, False otherwise
        """
        url = f"{self.base_url}/home.html"
        headers = {
            'Cookie': f'user_id={self.cookie}',
            **self.get_auth_header()
        }
        try:
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Error checking cookie validity: {e}")
            return False

    def login(self) -> None:
        """Login to the gateway and get a new session cookie."""
        url = f"{self.base_url}/cgi-bin/admin"
        headers = self.get_auth_header()
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                self.cookie = response.cookies.get('user_id', '')
                self.config['cookie'] = self.cookie
                save_config(self.config)
                logger.info("Login successful")
            else:
                logger.error(f"Login failed with status code {response.status_code}")
                raise HTTPException(status_code=401, detail="Login failed")
        except requests.RequestException as e:
            logger.error(f"Login request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Login request failed: {str(e)}")
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get a list of all configured devices.
        
        Returns:
            List of device information dictionaries
        """
        return [
            {
                "name": name,
                "location": device["location"],
                "type": device["type"]
            } for name, device in self.config['devices'].items()
        ]
    
    def control_device(self, device_name: str, action: str, level: Optional[int] = None, 
                      ac_mode: Optional[str] = None, temperature: Optional[int] = None) -> Dict[str, Any]:
        """Control a device with the specified action.
        
        Args:
            device_name: Name of the device to control
            action: Action to perform (on, off, dim, set_mode, set_temperature)
            level: Brightness level for dimmers (0-100)
            ac_mode: AC mode (cool, heat, etc.)
            temperature: Temperature setting for AC
            
        Returns:
            Response from the gateway
            
        Raises:
            HTTPException: If the device is not found or control fails
        """
        if not self.is_cookie_valid():
            logger.info("Cookie invalid, logging in")
            self.login()

        device_config = self.config['devices'].get(device_name)
        if not device_config:
            logger.error(f"Device {device_name} not found in configuration")
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
            **self.get_auth_header()
        }

        try:
            logger.info(f"Controlling device {device_name} with action {action}")
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"Device control failed with status code {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="Device control failed")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Device control request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Device control request failed: {str(e)}")

    def read_device_status(self, device_name: str) -> Dict[str, Any]:
        """Read the status of a device.
        
        Args:
            device_name: Name of the device to read status from
            
        Returns:
            Status information from the device
            
        Raises:
            HTTPException: If the device is not found or status read fails
        """
        if not self.is_cookie_valid():
            logger.info("Cookie invalid, logging in")
            self.login()

        device_config = self.config['devices'].get(device_name)
        if not device_config:
            logger.error(f"Device {device_name} not found in configuration")
            raise HTTPException(status_code=404, detail=f"Device {device_name} not found in configuration")

        url = f"{self.base_url}/cgi-bin/rpc_bridge"
        
        if device_config['type'] == 'DIMMER':
            methods = ["RPC_ZCL_Get_OnOff", "RPC_ZCL_Get_Level"]
        elif device_config['type'] == 'SWITCH':
            methods = ["RPC_ZCL_Get_OnOff"]
        else:
            raise HTTPException(status_code=400, detail="Unsupported device type for status reading")

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

            try:
                logger.info(f"Reading status for device {device_name} with method {method}")
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"Device status read failed with status code {response.status_code}")
                    raise HTTPException(status_code=response.status_code, detail="Device status read failed")
                results[method] = response.json()
            except requests.RequestException as e:
                logger.error(f"Device status read request failed: {e}")
                raise HTTPException(status_code=500, detail=f"Device status read request failed: {str(e)}")

        return results
