"""Database connection management including SSH tunnel and connection pooling."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import asyncpg
from sshtunnel import SSHTunnelForwarder
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.settings = get_settings()
        self.pool: Optional[asyncpg.Pool] = None  # Pool of database connections
        self.tunnel: Optional[SSHTunnelForwarder] = None  # SSH tunnel for secure access
        
    async def connect(self) -> None:
        """
        Establish SSH tunnel and create connection pool.
        
        This method:
        1. Creates an SSH tunnel to the database server for secure access
        2. Establishes a pool of database connections through the tunnel
        
        Raises:
            Exception: If connection fails, cleanup is performed and error is re-raised
        """
        try:
            # Setup SSH tunnel which forwards a local port to the remote database port
            self.tunnel = SSHTunnelForwarder(
                (self.settings.SSH_HOST, self.settings.SSH_PORT),
                ssh_username=self.settings.SSH_USER,
                ssh_pkey=self.settings.SSH_KEY_PATH,
                remote_bind_address=(self.settings.DB_HOST, self.settings.DB_PORT)
            )
            self.tunnel.start()
            
            # Create a pool of database connections through the SSH tunnel
            # The pool maintains a minimum and maximum number of connections
            self.pool = await asyncpg.create_pool(
                user=self.settings.DB_USER,
                password=self.settings.DB_PASS,
                database=self.settings.DB_NAME,
                host='127.0.0.1',  # Connect via local tunnel endpoint
                port=self.tunnel.local_bind_port,
                min_size=self.settings.DB_POOL_MIN_SIZE,
                max_size=self.settings.DB_POOL_MAX_SIZE,
            )
            logger.info("Database connection established", 
                       local_port=self.tunnel.local_bind_port)
            
        except Exception as e:
            logger.error("Failed to establish database connection", error=str(e))
            await self.disconnect()
            raise
    
    async def disconnect(self) -> None:
        """Close pool and tunnel."""
        if self.pool:
            await self.pool.close()
        if self.tunnel:
            self.tunnel.stop()
        logger.info("Database connection closed")
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a connection with transaction."""
        if not self.pool:
            raise RuntimeError("Database not connected")
            
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

# Global database connection instance
db = DatabaseConnection()