import os
import json
import yaml
import requests
import re
from packaging import version

def get_latest_tag(repo_owner, repo_name):
    """Obtém a última versão estável de uma imagem (ignora tags com 'beta')."""
    tags_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/tags'
    try:
        response = requests.get(tags_url)
        response.raise_for_status()
        tags = response.json()

        # Mantém apenas tags que tenham número e não contenham "beta"
        version_tags = [
            tag["name"]
            for tag in tags
            if re.search(r'\d', tag["name"]) and "beta" not in tag["name"].lower()
        ]

        if not version_tags:
            print(f"Nenhuma tag estável encontrada para {repo_owner}/{repo_name}.")
            return None

        # Ordena semanticamente (ex.: 2.10 > 2.9)
        version_tags = sorted(version_tags, key=version.parse, reverse=True)

        return version_tags[0]

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o GitHub: {e}")
        return None

def process_file(file_path, file_format):
    """Processa o arquivo e atualiza a versão da imagem."""
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
            repo_owner, repo_name = config["image"].split("/")
            print(f"Obtendo a última versão estável de {repo_owner}/{repo_name}")
            latest_tag = get_latest_tag(repo_owner, repo_name)

            if latest_tag:
                print(f"A versão estável mais recente é {latest_tag}")
                if config["version"] != latest_tag:
                    print(f"Atualizando {file_path} de {config['version']} para {latest_tag}")
                    config['version'] = latest_tag
                    with open(file_path, 'w') as f:
                        if file_format == 'yaml':
                            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                        elif file_format == 'json':
                            json.dump(config, f, indent=2)
            else:
                print(f"Não foi possível atualizar {file_path}.")
        else:
            print(f"Arquivo {file_path} não contém 'image' ou 'version'.")
    except Exception as e:
        print(f"Erro ao processar o arquivo {file_path}: {e}")

# Percorre todos os arquivos na árvore de diretórios
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('config.yaml'):
            process_file(os.path.join(root, file), 'yaml')
        elif file.endswith('config.json'):
            process_file(os.path.join(root, file), 'json')
