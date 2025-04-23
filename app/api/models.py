from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DeviceControl(BaseModel):
    """Model for device control requests."""
    device_name: str = Field(..., description="Name of the device to control")
    action: str = Field(..., description="Action to perform (on, off, dim, set_mode, set_temperature)")
    level: Optional[int] = Field(None, description="Brightness level for dimmers (0-100)")
    ac_mode: Optional[str] = Field(None, description="AC mode (cool, heat, etc.)")
    temperature: Optional[int] = Field(None, description="Temperature setting for AC")

class DeviceInfo(BaseModel):
    """Model for device information."""
    name: str = Field(..., description="Device name")
    location: str = Field(..., description="Device location")
    type: str = Field(..., description="Device type (DIMMER, SWITCH, AC)")

class DeviceList(BaseModel):
    """Model for list of devices."""
    devices: List[DeviceInfo] = Field(..., description="List of devices")

class DeviceStatusResponse(BaseModel):
    """Model for device status response."""
    status: str = Field(..., description="Status of the request")
    result: Dict[str, Any] = Field(..., description="Status information from the device")

class DeviceControlResponse(BaseModel):
    """Model for device control response."""
    status: str = Field(..., description="Status of the request")
    result: Dict[str, Any] = Field(..., description="Result of the control operation")
