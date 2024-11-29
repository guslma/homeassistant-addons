import os
import json
import yaml
import requests

def get_latest_and_previous_tag(repo_name):
    """Obtém a última tag de versão e a versão anterior de uma imagem Docker no Docker Hub."""
    tags_url = f'https://hub.docker.com/v2/repositories/{repo_name}/tags'
    try:
        response = requests.get(tags_url)
        response.raise_for_status()  # Levanta uma exceção se houver erro na requisição
        tags = response.json().get('results', [])
        
        # Filtra as tags que têm números e não contêm "nvidia" ou "lite"
        version_tags = [
            tag['name'] for tag in tags
            if any(char.isdigit() for char in tag['name']) and
               "lite" not in tag['name'].lower() and
               "nvidia" not in tag['name'].lower()
        ]

        if not version_tags:
            print(f"Nenhuma tag válida encontrada para {repo_name}.")
            return None, None

        # Ordena as tags em ordem decrescente
        version_tags = sorted(version_tags, reverse=True)

        # Verifica se a tag "latest" está na lista
        if 'latest' in version_tags:
            latest_index = version_tags.index('latest')
            # Verifica se há uma tag anterior à "latest"
            if latest_index > 0:
                return version_tags[latest_index - 1], version_tags[latest_index]
            else:
                print("Não há versão anterior à 'latest'.")
                return None, version_tags[latest_index]
        elif version_tags:
            # Retorna a última e a segunda última versão
            return version_tags[0], version_tags[1] if len(version_tags) > 1 else None
        else:
            print(f"Nenhuma tag encontrada para {repo_name}.")
            return None, None

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
                print(f"A versão anterior à 'latest' para {config['image']} é {previous_tag}")
                if config['version'] != previous_tag:
                    print(f"Atualizando {file_path} de {config['version']} para {previous_tag}")
                    config['version'] = previous_tag
                    with open(file_path, 'w') as f:
                        if file_format == 'yaml':
                            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                        elif file_format == 'json':
                            json.dump(config, f, indent=2)
            else:
                print(f"Não foi possível encontrar uma versão anterior à 'latest' para {config['image']}.")
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
