"""
Phase 14: Network Utilities
Validates external internet connectivity before allowing engine loops to execute.
"""
import socket
import logging

logger = logging.getLogger(__name__)


def is_network_available(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """
    Checks if the external internet is reachable by opening a TCP connection to Google DNS.
    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        return True
    except socket.error as e:
        logger.warning(f"Network availability check failed: {e}")
        return False
