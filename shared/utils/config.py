"""
Configuration management for Gergy MCP infrastructure.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import yaml

@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class RedisConfig:
    """Redis configuration."""
    url: str
    max_connections: int = 10
    socket_timeout: int = 30
    health_check_interval: int = 30

@dataclass
class ServerConfig:
    """Individual server configuration."""
    name: str
    domain: str
    daily_budget_limit: float
    enabled: bool = True
    debug: bool = False

@dataclass
class GergyConfig:
    """Main Gergy configuration."""
    database: DatabaseConfig
    redis: RedisConfig
    servers: Dict[str, ServerConfig]
    log_level: str = "INFO"
    environment: str = "development"

def load_config(config_path: Optional[str] = None) -> GergyConfig:
    """Load configuration from file and environment variables."""
    
    # Default configuration
    config_data = {
        "database": {
            "url": os.getenv("DATABASE_URL"),
            "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true",
            "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
            "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", "30")),
            "health_check_interval": int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))
        },
        "servers": {
            "financial": {
                "name": "gergy-financial",
                "domain": "financial",
                "daily_budget_limit": float(os.getenv("FINANCIAL_BUDGET_LIMIT", "15.0")),
                "enabled": os.getenv("FINANCIAL_ENABLED", "true").lower() == "true",
                "debug": os.getenv("FINANCIAL_DEBUG", "false").lower() == "true"
            },
            "family": {
                "name": "gergy-family",
                "domain": "family",
                "daily_budget_limit": float(os.getenv("FAMILY_BUDGET_LIMIT", "10.0")),
                "enabled": os.getenv("FAMILY_ENABLED", "true").lower() == "true",
                "debug": os.getenv("FAMILY_DEBUG", "false").lower() == "true"
            },
            "lifestyle": {
                "name": "gergy-lifestyle",
                "domain": "lifestyle",
                "daily_budget_limit": float(os.getenv("LIFESTYLE_BUDGET_LIMIT", "8.0")),
                "enabled": os.getenv("LIFESTYLE_ENABLED", "true").lower() == "true",
                "debug": os.getenv("LIFESTYLE_DEBUG", "false").lower() == "true"
            },
            "professional": {
                "name": "gergy-professional",
                "domain": "professional",
                "daily_budget_limit": float(os.getenv("PROFESSIONAL_BUDGET_LIMIT", "12.0")),
                "enabled": os.getenv("PROFESSIONAL_ENABLED", "true").lower() == "true",
                "debug": os.getenv("PROFESSIONAL_DEBUG", "false").lower() == "true"
            },
            "home": {
                "name": "gergy-home",
                "domain": "home",
                "daily_budget_limit": float(os.getenv("HOME_BUDGET_LIMIT", "8.0")),
                "enabled": os.getenv("HOME_ENABLED", "true").lower() == "true",
                "debug": os.getenv("HOME_DEBUG", "false").lower() == "true"
            }
        },
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }
    
    # Load from config file if provided
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            if config_file.suffix == '.json':
                with open(config_file) as f:
                    file_config = json.load(f)
            elif config_file.suffix in ['.yml', '.yaml']:
                with open(config_file) as f:
                    file_config = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")
            
            # Merge file config with defaults
            config_data = _merge_config(config_data, file_config)
    
    # Validate required configuration
    if not config_data["database"]["url"]:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Parse into dataclasses
    database_config = DatabaseConfig(**config_data["database"])
    redis_config = RedisConfig(**config_data["redis"])
    
    servers = {}
    for server_name, server_data in config_data["servers"].items():
        servers[server_name] = ServerConfig(**server_data)
    
    return GergyConfig(
        database=database_config,
        redis=redis_config,
        servers=servers,
        log_level=config_data["log_level"],
        environment=config_data["environment"]
    )

def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge configuration dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    
    return result

def save_config(config: GergyConfig, config_path: str):
    """Save configuration to file."""
    config_file = Path(config_path)
    
    # Convert to dictionary
    config_dict = {
        "database": {
            "url": config.database.url,
            "echo": config.database.echo,
            "pool_size": config.database.pool_size,
            "max_overflow": config.database.max_overflow
        },
        "redis": {
            "url": config.redis.url,
            "max_connections": config.redis.max_connections,
            "socket_timeout": config.redis.socket_timeout,
            "health_check_interval": config.redis.health_check_interval
        },
        "servers": {},
        "log_level": config.log_level,
        "environment": config.environment
    }
    
    for server_name, server_config in config.servers.items():
        config_dict["servers"][server_name] = {
            "name": server_config.name,
            "domain": server_config.domain,
            "daily_budget_limit": server_config.daily_budget_limit,
            "enabled": server_config.enabled,
            "debug": server_config.debug
        }
    
    # Save based on file extension
    if config_file.suffix == '.json':
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
    elif config_file.suffix in ['.yml', '.yaml']:
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    else:
        raise ValueError(f"Unsupported config file format: {config_file.suffix}")