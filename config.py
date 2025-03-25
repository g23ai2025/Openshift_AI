import os
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class ClusterConfig:
    name: str
    url: str
    token: str
    namespace: str

class Config:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Load clusters configuration
        self.clusters = self._load_clusters()
    
    def _load_clusters(self) -> List[ClusterConfig]:
        clusters = []
        
        # Add default cluster
        default_cluster = ClusterConfig(
            name=os.getenv('DEFAULT_CLUSTER_NAME', 'default'),
            url=os.getenv('DEFAULT_CLUSTER_URL', ''),
            token=os.getenv('DEFAULT_CLUSTER_TOKEN', ''),
            namespace=os.getenv('DEFAULT_CLUSTER_NAMESPACE', '')
        )
        clusters.append(default_cluster)
        
        # Find all cluster configurations
        env_vars = os.environ
        cluster_names = set()
        
        # Find all cluster names from environment variables
        for key in env_vars:
            if key.startswith('CLUSTER_') and key.endswith('_NAME'):
                cluster_name = env_vars[key]
                if cluster_name != default_cluster.name:  # Skip if it's the default cluster
                    cluster_names.add(cluster_name)
        
        # Load configuration for each cluster
        for name in cluster_names:
            prefix = f'CLUSTER_{name.upper()}_'
            if all(os.getenv(f'{prefix}{prop}') for prop in ['URL', 'TOKEN', 'NAMESPACE']):
                clusters.append(ClusterConfig(
                    name=name,
                    url=os.getenv(f'{prefix}URL'),
                    token=os.getenv(f'{prefix}TOKEN'),
                    namespace=os.getenv(f'{prefix}NAMESPACE')
                ))
        
        return clusters

# Create global configuration instance
config = Config()
