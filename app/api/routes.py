from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.api.models import DeviceControl, DeviceList, DeviceStatusResponse, DeviceControlResponse
from app.core.backend import SchneiderGatewayBackend
from app.core.config import settings

# Create router
router = APIRouter(tags=["devices"])

# Backend instance
backend = SchneiderGatewayBackend(settings.CONFIG_FILE)

@router.get("/devices", response_model=DeviceList, summary="Get all devices")
async def get_devices():
    """
    Get a list of all configured devices.
    
    Returns:
        A list of all devices with their name, location, and type.
    """
    return {"devices": backend.get_devices()}

@router.get("/device_status/{device_name}", response_model=DeviceStatusResponse, summary="Get device status")
async def get_device_status(device_name: str):
    """
    Get the status of a specific device.
    
    Args:
        device_name: Name of the device to get status for
        
    Returns:
        Status information from the device
        
    Raises:
        HTTPException: If the device is not found or status read fails
    """
    try:
        result = backend.read_device_status(device_name)
        return {"status": "success", "result": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control_device", response_model=DeviceControlResponse, summary="Control a device")
async def control_device(device_control: DeviceControl):
    """
    Control a device with the specified action.
    
    Args:
        device_control: Device control parameters
            - device_name: Name of the device to control
            - action: Action to perform (on, off, dim, set_mode, set_temperature)
            - level: Brightness level for dimmers (0-100)
            - ac_mode: AC mode (cool, heat, etc.)
            - temperature: Temperature setting for AC
            
    Returns:
        Result of the control operation
        
    Raises:
        HTTPException: If the device is not found or control fails
    """
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
