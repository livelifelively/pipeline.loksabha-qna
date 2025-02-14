import os
import debugpy
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def setup_debugger(
    host: Optional[str] = None,
    port: Optional[int] = None,
    wait_for_client: Optional[bool] = None
) -> None:
    """
    Set up the debugger for remote debugging.
    
    Configuration can be provided via arguments or environment variables:
    - DEBUG_HOST: Host to listen on (default: "0.0.0.0")
    - DEBUG_PORT: Port to listen on (default: 5678)
    - DEBUG_WAIT: Whether to wait for client (default: "true")
    
    Args:
        host: Host to listen on. Overrides DEBUG_HOST
        port: Port to listen on. Overrides DEBUG_PORT
        wait_for_client: Whether to wait for debugger. Overrides DEBUG_WAIT
    """
    if not os.getenv("DEBUG_ENABLED", "").lower() in ("true", "1", "yes"):
        return

    try:
        debug_host = host or os.getenv("DEBUG_HOST", "0.0.0.0")
        debug_port = port or int(os.getenv("DEBUG_PORT", "5678"))
        should_wait = wait_for_client if wait_for_client is not None else \
                     os.getenv("DEBUG_WAIT", "true").lower() in ("true", "1", "yes")

        debugpy.listen((debug_host, debug_port))
        logger.info(f"🔧 Debugger listening on {debug_host}:{debug_port}")
        
        if should_wait:
            print("⏳ Waiting for debugger to attach...")
            debugpy.wait_for_client()
            print("🔍 Debugger attached!")
            
    except Exception as e:
        logger.error(f"Failed to setup debugger: {e}")
        print(f"⚠️  Debug setup failed: {e}") 