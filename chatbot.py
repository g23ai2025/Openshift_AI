import os
from openai import OpenAI
from openshift_mcp import OpenshiftContext, OpenshiftMCP
from config import config
import json
from typing import Dict, Any, List

def initialize_openshift() -> OpenshiftMCP:
    """Initialize OpenShift MCP with clusters from config"""
    clusters = []
    
    for cluster_config in config.clusters:
        if cluster_config.url and cluster_config.token and cluster_config.namespace:
            clusters.append(OpenshiftContext(
                name=cluster_config.name,
                api_url=cluster_config.url,
                token=cluster_config.token,
                namespace=cluster_config.namespace
            ))
    
    if not clusters:
        raise ValueError("No valid cluster configurations found in .env file")
    
    return OpenshiftMCP(clusters)

def format_openai_prompt(resource_type: str, data: dict) -> str:
    """Format the prompt to get structured responses"""
    return f"""Analyze the OpenShift {resource_type} data and provide a structured summary in this exact format:

SUMMARY
- One-line overview of what you found

RESOURCES [{resource_type.upper()}]
- List each resource with name and type
- Include only key attributes like status, image, or ports
- Max 3 attributes per resource

STATUS
- Running/Failed/Pending count (for pods)
- Available/Total replicas (for deployments)
- Active/Inactive status (for services)

Do not include any other information. Keep each bullet point to one line.
Data: {json.dumps(data, indent=2)}"""

def format_response(response: str) -> str:
    """Format the response with proper spacing and separators"""
    sections = response.split('\n\n')
    formatted_sections = []
    
    for section in sections:
        if section.strip():
            formatted_sections.append(section.strip())
    
    return '\n\n' + '\n\n'.join(formatted_sections)

def get_openai_response(client: OpenAI, system_prompt: str, user_message: str, context_data: dict = None) -> str:
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    if context_data:
        resource_type = "resource"
        if "pod" in user_message:
            resource_type = "pods"
        elif "service" in user_message:
            resource_type = "services"
        elif "deployment" in user_message:
            resource_type = "deployments"
        elif "quota" in user_message:
            resource_type = "resource quotas"
        elif "configmap" in user_message:
            resource_type = "config maps"
            
        formatted_prompt = format_openai_prompt(resource_type, context_data)
        messages.append({"role": "system", "content": formatted_prompt})
    
    messages.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.5,
        max_tokens=300
    )
    return format_response(response.choices[0].message.content)

def print_help():
    """Print available commands and usage information"""
    print("\n📚 Commands:")
    print("pods       → List all pods")
    print("services   → List all services")
    print("deployments→ List all deployments")
    print("quotas     → Show resource quotas")
    print("configmaps → List config maps")
    print("clusters   → List available clusters")
    print("use <name> → Switch to cluster")
    print("help       → Show commands")
    print("exit       → Quit")

def main():
    # Initialize OpenAI client
    client = OpenAI(api_key=config.openai_api_key)
    
    # Initialize OpenShift MCP
    openshift = initialize_openshift()
    
    system_prompt = """You are an OpenShift cluster analyzer. Provide only the requested information in a structured format.
    Keep responses concise and focused on facts. Do not include explanations or technical details unless specifically asked."""
    
    print("🤖 OpenShift Assistant")
    print(f"Current cluster: {openshift.get_current_context()}")
    print_help()
    
    while True:
        try:
            user_input = input("\n👤 Command: ").strip().lower()
            
            if user_input == 'exit':
                print("👋 Goodbye!")
                break
                
            if user_input == 'help':
                print_help()
                continue
                
            if user_input == 'clusters':
                print("\n🌐 Available Clusters:")
                current = openshift.get_current_context()
                for cluster in openshift.list_contexts():
                    print(f"{'→' if cluster == current else ' '} {cluster}")
                continue
                
            if user_input.startswith('use '):
                cluster_name = user_input[4:].strip()
                if openshift.switch_context(cluster_name):
                    print(f"\n✅ Switched to cluster: {cluster_name}")
                else:
                    print(f"\n❌ Cluster not found: {cluster_name}")
                continue
            
            print("\n🔄 Processing...")
            
            # Fetch relevant data based on user input
            context_data = None
            try:
                if 'pod' in user_input:
                    context_data = openshift.get_pods()
                elif 'service' in user_input:
                    context_data = openshift.get_services()
                elif 'deployment' in user_input:
                    context_data = openshift.get_deployments()
                elif 'quota' in user_input:
                    context_data = openshift.get_resource_quotas()
                elif 'configmap' in user_input:
                    context_data = openshift.get_config_maps()
            
                if context_data:
                    response = get_openai_response(client, system_prompt, user_input, context_data)
                    print(f"\n📊 Results from cluster: {openshift.get_current_context()}")
                    print("─" * 50)
                    print(response)
                    print("─" * 50)
                else:
                    print("\n❌ No matching resources found. Try 'help' for available commands.")
                
            except Exception as e:
                print(f"\n❌ OpenShift API Error: {str(e)}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
