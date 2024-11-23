import os
import json
import yaml
import requests

def get_latest_tag(repo_name):
    """Obtém a última tag de versão de uma imagem Docker no Docker Hub ou no GitHub para casos específicos."""
    # Caso especial para o repositório koush/scrypted
    if repo_name == "koush/scrypted":
        print(f"Getting latest version of {repo_name} from GitHub")
        return get_latest_tag_from_github(repo_name)
    
    # Busca padrão no Docker Hub
    print(f"Getting latest version of {repo_name} from Docker Hub")
    tags_url = f'https://hub.docker.com/v2/repositories/{repo_name}/tags'
    response = requests.get(tags_url)
    response.raise_for_status()
    
    tags = response.json().get('results', [])
    version_tags = [tag['name'] for tag in tags if any(char.isdigit() for char in tag['name'])]
    
    if version_tags:
        latest_tag = sorted(version_tags, reverse=True)[0]
        print(f"Latest version of {repo_name} is {latest_tag}")
        return latest_tag
    else:
        print(f"No version tags found for {repo_name} on Docker Hub.")
        return None

def get_latest_tag_from_github(repo_name):
    """Obtém a última tag de versão de um repositório no GitHub."""
    tags_url = f'https://api.github.com/repos/{repo_name}/tags'
    response = requests.get(tags_url)
    response.raise_for_status()
    
    tags = response.json()
    version_tags = [tag['name'] for tag in tags if any(char.isdigit() for char in tag['name'])]
    
    if version_tags:
        latest_tag = sorted(version_tags, reverse=True)[0]
        print(f"Latest version of {repo_name} on GitHub is {latest_tag}")
        return latest_tag
    else:
        print(f"No version tags found for {repo_name} on GitHub.")
        return None

    if 'image' in config:
        print(f"Getting latest version of {config['image']} from Docker Hub")
        latest_tag = get_latest_tag(config['image'])
        print(f"Latest version of {config['image']} is {latest_tag}")
        
        if latest_tag and config.get('version') != latest_tag:
            print(f"Updating {file_path} from {config.get('version')} to {latest_tag}")
            config['version'] = latest_tag
            with open(file_path, 'w') as f:
                if file_format == 'yaml':
                    yaml.dump(config, f)
                elif file_format == 'json':
                    json.dump(config, f, indent=2)

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('config.yaml'):
            process_file(os.path.join(root, file), 'yaml')
        elif file.endswith('config.json'):
            process_file(os.path.join(root, file), 'json')
