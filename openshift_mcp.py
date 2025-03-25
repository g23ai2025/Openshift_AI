from dataclasses import dataclass
from typing import Dict, List, Optional
import requests
import urllib3
from collections import defaultdict

@dataclass
class OpenshiftContext:
    api_url: str
    token: str
    namespace: str
    name: str  # Friendly name for the cluster
    verify_ssl: bool = False

class OpenshiftMCP:
    def __init__(self, contexts: List[OpenshiftContext]):
        self.contexts = {ctx.name: ctx for ctx in contexts}
        self.current_context = contexts[0].name if contexts else None
        
        if any(not ctx.verify_ssl for ctx in contexts):
            urllib3.disable_warnings()
    
    def switch_context(self, name: str) -> bool:
        """Switch to a different cluster context"""
        if name in self.contexts:
            self.current_context = name
            return True
        return False
    
    def list_contexts(self) -> List[str]:
        """List all available cluster contexts"""
        return list(self.contexts.keys())
    
    def get_current_context(self) -> str:
        """Get current cluster context name"""
        return self.current_context
    
    def _get_headers(self) -> Dict:
        """Get headers for current context"""
        ctx = self.contexts[self.current_context]
        return {"Authorization": f"Bearer {ctx.token}"}
    
    def _get_base_url(self) -> str:
        """Get base URL for current context"""
        ctx = self.contexts[self.current_context]
        return f"{ctx.api_url}/api/v1/namespaces/{ctx.namespace}"
    
    def get_pods(self) -> Dict:
        """Get all pods in the namespace"""
        ctx = self.contexts[self.current_context]
        response = requests.get(
            f"{self._get_base_url()}/pods",
            headers=self._get_headers(),
            verify=ctx.verify_ssl
        )
        return self._handle_response(response)
    
    def get_services(self) -> Dict:
        """Get all services in the namespace"""
        ctx = self.contexts[self.current_context]
        response = requests.get(
            f"{self._get_base_url()}/services",
            headers=self._get_headers(),
            verify=ctx.verify_ssl
        )
        return self._handle_response(response)
    
    def get_deployments(self) -> Dict:
        """Get all deployments in the namespace"""
        ctx = self.contexts[self.current_context]
        response = requests.get(
            f"{ctx.api_url}/apis/apps/v1/namespaces/{ctx.namespace}/deployments",
            headers=self._get_headers(),
            verify=ctx.verify_ssl
        )
        return self._handle_response(response)
    
    def get_resource_quotas(self) -> Dict:
        """Get resource quotas for the namespace"""
        ctx = self.contexts[self.current_context]
        response = requests.get(
            f"{self._get_base_url()}/resourcequotas",
            headers=self._get_headers(),
            verify=ctx.verify_ssl
        )
        return self._handle_response(response)
    
    def get_config_maps(self) -> Dict:
        """Get all config maps in the namespace"""
        ctx = self.contexts[self.current_context]
        response = requests.get(
            f"{self._get_base_url()}/configmaps",
            headers=self._get_headers(),
            verify=ctx.verify_ssl
        )
        return self._handle_response(response)
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and errors"""
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
