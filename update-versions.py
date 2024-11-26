import os
import json
import yaml
import requests

def get_latest_tag(repo_name):
    """Obtém a última tag de versão de uma imagem Docker no Docker Hub."""
    tags_url = f'https://hub.docker.com/v2/repositories/{repo_name}/tags'
    try:
        response = requests.get(tags_url)
        response.raise_for_status()  # Levanta uma exceção se houver erro na requisição
        tags = response.json().get('results', [])
        # Filtra as tags que têm números e não contêm "nvidia" ou "lite"
        version_tags = [
            tag['name'] for tag in tags
            if any(char.isdigit() for char in tag['name']) and
               "nvidia" not in tag['name'].lower() and
               "lite" not in tag['name'].lower()
        ]
        return sorted(version_tags, reverse=True)[0] if version_tags else None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o Docker Hub: {e}")
        return None

def process_file(file_path, file_format):
    """Processa o arquivo de configuração, atualizando a versão da imagem."""
    try:
        with open(file_path, 'r') as f:
            if file_format == 'yaml':
                config = yaml.safe_load(f)
            elif file_format == 'json':
                config = json.load(f)
            else:
                print(f"Formato não suportado para {file_path}")
                return

        if 'image' in config and 'version' in config:
            print(f"Obtendo a última versão da imagem {config['image']} do Docker Hub")
            latest_tag = get_latest_tag(config['image'])
            if latest_tag:
                print(f"Última versão de {config['image']} é {latest_tag}")
                if config['version'] != latest_tag:
                    print(f"Atualizando {file_path} de {config['version']} para {latest_tag}")
                    config['version'] = latest_tag
                    with open(file_path, 'w') as f:
                        if file_format == 'yaml':
                            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                        elif file_format == 'json':
                            json.dump(config, f, indent=2)
        else:
            print(f"Arquivo {file_path} não contém 'image' ou 'version'.")
    except Exception as e:
        print(f"Erro ao processar o arquivo {file_path}: {e}")

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('config.yaml'):
            process_file(os.path.join(root, file), 'yaml')
        elif file.endswith('config.json'):
            process_file(os.path.join(root, file), 'json')
