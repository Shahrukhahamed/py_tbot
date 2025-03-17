import requests
from config.settings import settings
from src.utils.logger import logger
from typing import List, Optional, Dict

class RPCClient:
    def __init__(self, chain: str):
        """Initialize the RPC client with the appropriate chain endpoint."""
        try:
            self.endpoint = settings.BLOCKCHAINS[chain]['rpc']
        except KeyError:
            logger.log(f"Error: Blockchain '{chain}' not found in settings.")
            raise ValueError(f"Invalid blockchain: {chain}")

    def call(self, method: str, params: Optional[List] = None) -> Dict:
        """
        Makes a JSON-RPC call to the blockchain endpoint.

        Args:
            method: The RPC method to call.
            params: A list of parameters for the method (default: empty list).

        Returns:
            A dictionary containing the JSON response from the RPC call.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }

        try:
            # Sending POST request with timeout to avoid hanging
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Checking for valid JSON response
            response_data = response.json()
            
            # Log the response (optional, for debugging)
            logger.log(f"RPC Call: {method} with params {params} - Response: {response_data}")
            
            # Validate response structure if needed (e.g., check if 'result' exists)
            if 'result' in response_data:
                return response_data
            else:
                logger.log(f"Error: Invalid RPC response for method {method}. Response: {response_data}")
                return {}
                
        except requests.exceptions.RequestException as e:
            # Catching all request-related exceptions and logging
            logger.log(f"Error during RPC call to {self.endpoint}: {e}")
            return {}
        except ValueError as e:
            # Handling JSON parsing errors
            logger.log(f"Invalid JSON response from {self.endpoint}: {e}")
            return {}