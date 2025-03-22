"""
SSH tunnel utilities for database connection.
Provides functions for creating and managing SSH tunnels.
"""
from sshtunnel import SSHTunnelForwarder
from typing import Optional
from ..config import get_database_config

class SSHError(Exception):
    """Custom exception for SSH-related errors."""
    pass

def create_ssh_tunnel() -> SSHTunnelForwarder:
    """
    Create and start an SSH tunnel for database connection.
    
    Returns:
        SSHTunnelForwarder: The started SSH tunnel
    
    Raises:
        SSHError: If tunnel creation or startup fails
        ValueError: If required configuration is missing
    """
    try:
        config = get_database_config()
        
        # Validate required SSH configuration
        required_fields = ["SSH_HOST", "SSH_USER", "SSH_KEY_PATH"]
        missing_fields = [field for field in required_fields 
                         if not config.get(field)]
        if missing_fields:
            raise ValueError(f"Missing required SSH configuration: {', '.join(missing_fields)}")
        
        # Create and start tunnel
        tunnel = SSHTunnelForwarder(
            (config["SSH_HOST"], config["SSH_PORT"]),
            ssh_username=config["SSH_USER"],
            ssh_pkey=config["SSH_KEY_PATH"],
            remote_bind_address=(config["DB_HOST"], config["DB_PORT"])
        )
        
        try:
            tunnel.start()
        except Exception as e:
            raise SSHError(f"Failed to start SSH tunnel: {str(e)}")
            
        if not tunnel.is_active:
            raise SSHError("SSH tunnel failed to activate")
            
        return tunnel
        
    except Exception as e:
        if isinstance(e, (SSHError, ValueError)):
            raise
        raise SSHError(f"Unexpected error creating SSH tunnel: {str(e)}")

def close_ssh_tunnel(tunnel: Optional[SSHTunnelForwarder]) -> None:
    """
    Safely close an SSH tunnel.
    
    Args:
        tunnel: The SSH tunnel to close
    
    Raises:
        SSHError: If tunnel closure fails
    """
    if not tunnel:
        return
        
    try:
        if tunnel.is_active:
            tunnel.stop()
            if tunnel.is_active:
                raise SSHError("SSH tunnel failed to close properly")
    except Exception as e:
        if isinstance(e, SSHError):
            raise
        raise SSHError(f"Error closing SSH tunnel: {str(e)}") 