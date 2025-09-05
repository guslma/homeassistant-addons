import os
import json
import yaml
import requests
import re

def get_latest_stable_tag(repo_owner, repo_name):
    """Obtém a última tag estável (sem 'beta') de um repositório no GitHub"""
    tags_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/tags'
    
    try:
        response = requests.get(tags_url)
        response.raise_for_status()
        tags = response.json()
        
        # Filtra tags que contêm números e não contêm 'beta'
        stable_tags = [
            tag["name"]
            for tag in tags
            if re.search(r'\d', tag["name"]) and 'beta' not in tag["name"].lower()
        ]

        if not stable_tags:
            print(f"Nenhuma tag estável encontrada para {repo_owner}/{repo_name}")
            return None

        # Ordena as tags e retorna a mais recente
        stable_tags.sort(reverse=True)
        return stable_tags[0]

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o GitHub para {repo_owner}/{repo_name}: {e}")
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

        # Verifica se o arquivo tem a estrutura esperada
        if not all(key in config for key in ['image', 'version']):
            print(f"Arquivo {file_path} não contém 'image' e 'version'")
            return

        # Extrai owner e nome do repositório
        if '/' not in config["image"]:
            print(f"Formato de imagem inválido em {file_path}: {config['image']}")
            return
            
        repo_owner, repo_name = config["image"].split("/")
        
        print(f"Buscando última versão estável de {repo_owner}/{repo_name}")
        latest_tag = get_latest_stable_tag(repo_owner, repo_name)

        if not latest_tag:
            return

        print(f"Versão atual: {config['version']}, Última estável: {latest_tag}")
        
        # Atualiza apenas se for diferente
        if config["version"] != latest_tag:
            print(f"Atualizando {file_path} para versão {latest_tag}")
            config['version'] = latest_tag
            
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
