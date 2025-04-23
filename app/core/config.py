import os
import yaml
import logging
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings."""
    APP_NAME: str = "Schneider Gateway API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API for controlling and monitoring Schneider Gateway devices"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # CORS settings
    CORS_ORIGINS: list = ["*"]

    # Config file path
    CONFIG_FILE: str = os.getenv("CONFIG_FILE", "config.yaml")

    class Config:
        env_file = ".env"

settings = Settings()

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(settings.CONFIG_FILE, 'r') as file:
            config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {settings.CONFIG_FILE}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file {settings.CONFIG_FILE} not found")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to YAML file."""
    try:
        with open(settings.CONFIG_FILE, 'w') as file:
            yaml.dump(config, file)
            logger.info(f"Configuration saved to {settings.CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise
