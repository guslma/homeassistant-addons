import os
import json
import yaml
import requests
import re

def get_latest_and_previous_tag(repo_name):
    """Obtém a tag 'latest' e a versão anterior de uma imagem Docker no Docker Hub, ignorando tags inválidas."""
    tags_url = f'https://hub.docker.com/v2/repositories/{repo_name}/tags'
    try:
        response = requests.get(tags_url)
        response.raise_for_status()  # Levanta uma exceção se houver erro na requisição
        tags = response.json().get('results', [])
        
        # Filtra tags que possuem números, com ou sem palavras adicionais (ex.: 1.0, 1.0-full, mas ignora 'full' ou 'beta')
        version_tags = [
            tag['name'] 
            for tag in tags 
            if re.search(r'\d', tag['name'])  # Verifica se contém algum número
        ]

        if not version_tags:
            print(f"Nenhuma tag válida encontrada para {repo_name}.")
            return None, None

        # Ordena as tags alfabeticamente, para que números fiquem antes de palavras
        version_tags = sorted(version_tags, reverse=True)

        # Verifica se a tag "latest" está na lista de todas as tags
        all_tags = [tag['name'] for tag in tags]
        if 'latest' in all_tags:
            # Retorna a tag mais recente válida e a imediatamente anterior
            return version_tags[0], 'latest'
        else:
            print(f"A tag 'latest' não foi encontrada para {repo_name}.")
            return version_tags[0], None

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o Docker Hub: {e}")
        return None, None

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
            previous_tag, latest_tag = get_latest_and_previous_tag(config['image'])
            if previous_tag:
                print(f"A versão anterior à 'latest' de {config['image']} é {previous_tag}")
                if config['version'] != previous_tag:
                    print(f"Atualizando {file_path} de {config['version']} para {previous_tag}")
                    config['version'] = previous_tag
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
