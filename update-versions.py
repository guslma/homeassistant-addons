import os
import json
import yaml
import requests
import re
from datetime import datetime

def get_latest_release(repo_owner, repo_name):
    """Obtém a última release estável (sem 'beta') de um repositório no GitHub"""
    releases_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases'
    
    try:
        response = requests.get(releases_url)
        response.raise_for_status()
        releases = response.json()
        
        # Filtra releases que não são pré-releases e não contêm 'beta' no nome
        stable_releases = [
            release for release in releases
            if not release.get('prerelease', False) 
            and 'beta' not in release.get('name', '').lower()
            and 'beta' not in release.get('tag_name', '').lower()
        ]

        if not stable_releases:
            print(f"Nenhuma release estável encontrada para {repo_owner}/{repo_name}")
            return None

        # Ordena por data de publicação (mais recente primeiro)
        stable_releases.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        latest_release = stable_releases[0]
        return latest_release.get('tag_name')

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar GitHub para {repo_owner}/{repo_name}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None

def process_config_file(file_path, file_format):
    """Processa o arquivo de configuração e atualiza a versão se necessário"""
    try:
        with open(file_path, 'r') as f:
            if file_format == 'yaml':
                config = yaml.safe_load(f)
            elif file_format == 'json':
                config = json.load(f)
            else:
                return

        if not all(key in config for key in ['image', 'version']):
            print(f"Arquivo {file_path} não contém 'image' e 'version'")
            return

        if '/' not in config["image"]:
            print(f"Formato de imagem inválido em {file_path}: {config['image']}")
            return
            
        repo_owner, repo_name = config["image"].split("/")
        
        print(f"Buscando última release estável de {repo_owner}/{repo_name}")
        latest_release = get_latest_release(repo_owner, repo_name)

        if not latest_release:
            return

        print(f"Versão atual: {config['version']}, Última release: {latest_release}")
        
        # Atualiza apenas se for diferente
        if config["version"] != latest_release:
            print(f"Atualizando {file_path} para versão {latest_release}")
            config['version'] = latest_release
            
            with open(file_path, 'w') as f:
                if file_format == 'yaml':
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                elif file_format == 'json':
                    json.dump(config, f, indent=2)
                    
            print(f"Arquivo {file_path} atualizado com sucesso!")
        else:
            print(f"Arquivo {file_path} já está na versão mais recente")

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

# Processa arquivos de configuração
for root, dirs, files in os.walk('.'):
    for file in files:
        file_path = os.path.join(root, file)
        
        if file.endswith('config.yaml'):
            process_config_file(file_path, 'yaml')
        elif file.endswith('config.json'):
            process_config_file(file_path, 'json')
