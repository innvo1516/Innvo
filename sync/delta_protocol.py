import time
import json
import socket
import logging
from typing import Dict, Any, List

import config

logger = logging.getLogger("InnvoDeltaProtocol")

class DeltaProtocol:
    """
    Encapsulates micro-delta synchronization packets (< 50 KB)
    for distributed cross-device hive-mind coordination.
    """

    @staticmethod
    def get_device_id() -> str:
        hostname = socket.gethostname()
        platform_name = "termux" if config.IS_TERMUX else ("win" if config.IS_WINDOWS else "linux")
        return f"{hostname}_{platform_name}"

    @staticmethod
    def create_delta_packet(memories: List[Dict[str, Any]], 
                            skills: List[Dict[str, Any]], 
                            triples: List[Dict[str, Any]],
                            policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Packages incremental changes into a compact JSON packet.
        """
        packet = {
            "protocol_version": "1.0",
            "device_id": DeltaProtocol.get_device_id(),
            "timestamp": time.time(),
            "payload": {
                "memories": memories,
                "skills": skills,
                "triples": triples,
                "policy": policy
            }
        }
        return packet

    @staticmethod
    def validate_packet(packet: Dict[str, Any]) -> bool:
        if not isinstance(packet, dict):
            return False
        if "protocol_version" not in packet or "payload" not in packet:
            return False
        return True
