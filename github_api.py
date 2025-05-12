import os
import base64
import requests
from typing import Optional, List, Dict, Union
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Obtém o token do GitHub das variáveis de ambiente
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Verificação básica do token
if not GITHUB_TOKEN:
    print("AVISO: Token do GitHub não encontrado nas variáveis de ambiente.", file=sys.stderr)
    print("Configure a variável GITHUB_TOKEN no arquivo .env", file=sys.stderr)
    # Por segurança, não definir fallback token em produção
    raise ValueError("Token do GitHub é obrigatório. Configure a variável GITHUB_TOKEN.")

# Headers para a API do GitHub
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# URL base da API do GitHub
API_BASE_URL = "https://api.github.com"

def listar_repositorios(username: str = None) -> dict:
    """
    Lista todos os repositórios do usuário ou da organização.
    
    Args:
        username: Nome do usuário ou organização (opcional)
        
    Returns:
        dict: Informações sobre os repositórios
    """
    try:
        # Se o username não for fornecido, lista os repositórios do usuário autenticado
        if not username:
            url = f"{API_BASE_URL}/user/repos"
        else:
            url = f"{API_BASE_URL}/users/{username}/repos"
        
        # Parâmetros para obter mais informações e organizar por atualização
        params = {
            "sort": "updated",
            "direction": "desc",
            "per_page": 100
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        repos = response.json()
        resultado = {
            "sucesso": True,
            "mensagem": f"Encontrados {len(repos)} repositórios",
            "repositorios": []
        }
        
        for repo in repos:
            resultado["repositorios"].append({
                "id": repo.get("id"),
                "nome": repo.get("name"),
                "nome_completo": repo.get("full_name"),
                "url": repo.get("html_url"),
                "descricao": repo.get("description"),
                "privado": repo.get("private"),
                "default_branch": repo.get("default_branch"),
                "linguagem": repo.get("language"),
                "data_atualizacao": repo.get("updated_at")
            })
        
        return resultado
    
    except Exception as e:
        print(f"Erro ao listar repositórios: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao listar repositórios: {str(e)}"
        }

def listar_branches(repo_owner: str, repo_name: str) -> dict:
    """
    Lista todas as branches de um repositório.
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        
    Returns:
        dict: Informações sobre as branches
    """
    try:
        url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/branches"
        
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        branches = response.json()
        resultado = {
            "sucesso": True,
            "mensagem": f"Encontradas {len(branches)} branches",
            "branches": []
        }
        
        for branch in branches:
            resultado["branches"].append({
                "nome": branch.get("name"),
                "commit_sha": branch.get("commit", {}).get("sha")
            })
        
        return resultado
    
    except Exception as e:
        print(f"Erro ao listar branches: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao listar branches: {str(e)}"
        }

def listar_arquivos(repo_owner: str, repo_name: str, path: str = "", branch: str = None) -> dict:
    """
    Lista todos os arquivos e diretórios em um caminho específico do repositório.
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        path: Caminho para listar (opcional, padrão: raiz)
        branch: Nome da branch (opcional, usa a default se não fornecida)
        
    Returns:
        dict: Informações sobre os arquivos e diretórios
    """
    try:
        # Se branch não for fornecida, primeiro descobre a branch padrão
        if not branch:
            repo_info_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}"
            repo_response = requests.get(repo_info_url, headers=HEADERS)
            repo_response.raise_for_status()
            branch = repo_response.json().get("default_branch", "main")
        
        # URL para listar conteúdo
        url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{path}"
        params = {"ref": branch}
        
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        contents = response.json()
        
        # Se for um único arquivo, converte para lista
        if not isinstance(contents, list):
            contents = [contents]
        
        resultado = {
            "sucesso": True,
            "mensagem": f"Encontrados {len(contents)} itens no caminho '{path}'",
            "branch": branch,
            "itens": []
        }
        
        for item in contents:
            resultado["itens"].append({
                "nome": item.get("name"),
                "caminho": item.get("path"),
                "tipo": item.get("type"),  # "file" ou "dir"
                "tamanho": item.get("size") if item.get("type") == "file" else None,
                "url": item.get("html_url"),
                "sha": item.get("sha")
            })
        
        return resultado
    
    except Exception as e:
        print(f"Erro ao listar arquivos: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao listar arquivos: {str(e)}"
        }

def obter_conteudo_arquivo(repo_owner: str, repo_name: str, path: str, branch: str = None) -> dict:
    """
    Obtém o conteúdo de um arquivo específico do repositório.
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        path: Caminho do arquivo
        branch: Nome da branch (opcional, usa a default se não fornecida)
        
    Returns:
        dict: Conteúdo do arquivo e informações relacionadas
    """
    try:
        # Se branch não for fornecida, primeiro descobre a branch padrão
        if not branch:
            repo_info_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}"
            repo_response = requests.get(repo_info_url, headers=HEADERS)
            repo_response.raise_for_status()
            branch = repo_response.json().get("default_branch", "main")
        
        # URL para obter conteúdo
        url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{path}"
        params = {"ref": branch}
        
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        file_info = response.json()
        
        # Verifica se é um arquivo
        if file_info.get("type") != "file":
            return {
                "sucesso": False,
                "mensagem": f"O caminho '{path}' não é um arquivo"
            }
        
        # Decodifica o conteúdo do arquivo (Base64)
        content = base64.b64decode(file_info.get("content")).decode("utf-8")
        
        return {
            "sucesso": True,
            "mensagem": f"Conteúdo do arquivo '{path}' obtido com sucesso",
            "nome": file_info.get("name"),
            "caminho": file_info.get("path"),
            "tamanho": file_info.get("size"),
            "sha": file_info.get("sha"),
            "conteudo": content,
            "url": file_info.get("html_url"),
            "branch": branch
        }
    
    except Exception as e:
        print(f"Erro ao obter conteúdo do arquivo: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao obter conteúdo do arquivo: {str(e)}"
        }

def atualizar_arquivo(
    repo_owner: str, 
    repo_name: str, 
    path: str, 
    conteudo: str, 
    mensagem_commit: str, 
    branch: str = None,
    sha: str = None
) -> dict:
    """
    Atualiza ou cria um arquivo no repositório.
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        path: Caminho do arquivo
        conteudo: Novo conteúdo do arquivo
        mensagem_commit: Mensagem do commit
        branch: Nome da branch (opcional, usa a default se não fornecida)
        sha: SHA do arquivo existente (obrigatório para atualização, não para criação)
        
    Returns:
        dict: Informações sobre o resultado da operação
    """
    try:
        # Se branch não for fornecida, primeiro descobre a branch padrão
        if not branch:
            repo_info_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}"
            repo_response = requests.get(repo_info_url, headers=HEADERS)
            repo_response.raise_for_status()
            branch = repo_response.json().get("default_branch", "main")
        
        # Se o SHA não for fornecido, tenta obter o SHA do arquivo existente
        if not sha:
            try:
                file_info = obter_conteudo_arquivo(repo_owner, repo_name, path, branch)
                if file_info["sucesso"]:
                    sha = file_info["sha"]
            except:
                # Se o arquivo não existir, o SHA não é necessário (criação)
                pass
        
        # URL para atualizar/criar arquivo
        url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{path}"
        
        # Codifica o conteúdo para Base64
        content_bytes = conteudo.encode("utf-8")
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
        
        # Dados para a requisição
        data = {
            "message": mensagem_commit,
            "content": content_base64,
            "branch": branch
        }
        
        # Adiciona o SHA se estiver atualizando um arquivo existente
        if sha:
            data["sha"] = sha
            operacao = "atualizado"
        else:
            operacao = "criado"
        
        # Faz a requisição PUT para criar/atualizar o arquivo
        response = requests.put(url, headers=HEADERS, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "sucesso": True,
            "mensagem": f"Arquivo '{path}' {operacao} com sucesso",
            "commit": {
                "sha": result.get("commit", {}).get("sha"),
                "url": result.get("commit", {}).get("html_url")
            },
            "arquivo": {
                "nome": path.split("/")[-1],
                "caminho": path,
                "sha": result.get("content", {}).get("sha"),
                "url": result.get("content", {}).get("html_url")
            }
        }
    
    except Exception as e:
        print(f"Erro ao atualizar arquivo: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao atualizar arquivo: {str(e)}"
        }

def excluir_arquivo(
    repo_owner: str, 
    repo_name: str, 
    path: str, 
    mensagem_commit: str, 
    branch: str = None
) -> dict:
    """
    Exclui um arquivo do repositório.
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        path: Caminho do arquivo
        mensagem_commit: Mensagem do commit
        branch: Nome da branch (opcional, usa a default se não fornecida)
        
    Returns:
        dict: Informações sobre o resultado da operação
    """
    try:
        # Primeiro obtém o SHA do arquivo (obrigatório para exclusão)
        file_info = obter_conteudo_arquivo(repo_owner, repo_name, path, branch)
        
        if not file_info["sucesso"]:
            return file_info
        
        sha = file_info["sha"]
        
        # Se branch não foi fornecida, usa a que foi obtida na chamada anterior
        if not branch:
            branch = file_info["branch"]
        
        # URL para excluir arquivo
        url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{path}"
        
        # Dados para a requisição
        data = {
            "message": mensagem_commit,
            "sha": sha,
            "branch": branch
        }
        
        # Faz a requisição DELETE
        response = requests.delete(url, headers=HEADERS, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "sucesso": True,
            "mensagem": f"Arquivo '{path}' excluído com sucesso",
            "commit": {
                "sha": result.get("commit", {}).get("sha"),
                "url": result.get("commit", {}).get("html_url")
            }
        }
    
    except Exception as e:
        print(f"Erro ao excluir arquivo: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao excluir arquivo: {str(e)}"
        }

def criar_commit_multiplo(
    repo_owner: str,
    repo_name: str,
    mensagem_commit: str,
    alteracoes: List[Dict[str, str]],
    branch: str = None
) -> dict:
    """
    Cria um commit com múltiplas alterações (arquivos).
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        mensagem_commit: Mensagem do commit
        alteracoes: Lista de dicionários, cada um contendo 'path', 'conteudo' e opcionalmente 'sha'
        branch: Nome da branch (opcional, usa a default se não fornecida)
        
    Returns:
        dict: Informações sobre o resultado da operação
    """
    try:
        # Se branch não for fornecida, primeiro descobre a branch padrão
        if not branch:
            repo_info_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}"
            repo_response = requests.get(repo_info_url, headers=HEADERS)
            repo_response.raise_for_status()
            branch = repo_response.json().get("default_branch", "main")
        
        # Primeiro, obtém a referência da branch
        ref_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/git/refs/heads/{branch}"
        ref_response = requests.get(ref_url, headers=HEADERS)
        ref_response.raise_for_status()
        
        ref_sha = ref_response.json().get("object", {}).get("sha")
        
        # Em seguida, obtém o commit mais recente
        commit_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/git/commits/{ref_sha}"
        commit_response = requests.get(commit_url, headers=HEADERS)
        commit_response.raise_for_status()
        
        parent_sha = commit_response.json().get("sha")
        tree_sha = commit_response.json().get("tree", {}).get("sha")
        
        # Agora, cria uma nova árvore
        tree_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/git/trees"
        tree_data = {
            "base_tree": tree_sha,
            "tree": []
        }
        
        # Adiciona cada alteração à árvore
        for alteracao in alteracoes:
            path = alteracao.get("path")
            conteudo = alteracao.get("conteudo")
            
            # Codifica o conteúdo para Base64
            content_bytes = conteudo.encode("utf-8")
            content_base64 = base64.b64encode(content_bytes).decode("utf-8")
            
            tree_item = {
                "path": path,
                "mode": "100644",  # Modo para arquivo regular
                "type": "blob",
                "content": conteudo
            }
            
            tree_data["tree"].append(tree_item)
        
        # Cria a nova árvore
        tree_response = requests.post(tree_url, headers=HEADERS, json=tree_data)
        tree_response.raise_for_status()
        
        new_tree_sha = tree_response.json().get("sha")
        
        # Cria o novo commit
        commit_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/git/commits"
        commit_data = {
            "message": mensagem_commit,
            "parents": [parent_sha],
            "tree": new_tree_sha
        }
        
        commit_response = requests.post(commit_url, headers=HEADERS, json=commit_data)
        commit_response.raise_for_status()
        
        new_commit_sha = commit_response.json().get("sha")
        
        # Atualiza a referência da branch
        ref_update_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/git/refs/heads/{branch}"
        ref_data = {
            "sha": new_commit_sha,
            "force": False
        }
        
        ref_update_response = requests.patch(ref_update_url, headers=HEADERS, json=ref_data)
        ref_update_response.raise_for_status()
        
        return {
            "sucesso": True,
            "mensagem": f"Commit com {len(alteracoes)} alterações criado com sucesso",
            "commit": {
                "sha": new_commit_sha,
                "url": f"https://github.com/{repo_owner}/{repo_name}/commit/{new_commit_sha}",
                "mensagem": mensagem_commit
            },
            "arquivos_alterados": [alteracao.get("path") for alteracao in alteracoes]
        }
    
    except Exception as e:
        print(f"Erro ao criar commit múltiplo: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao criar commit múltiplo: {str(e)}"
        }

def criar_pull_request(
    repo_owner: str,
    repo_name: str,
    titulo: str,
    descricao: str,
    branch_origem: str,
    branch_destino: str
) -> dict:
    """
    Cria um pull request no repositório.
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        titulo: Título do pull request
        descricao: Descrição do pull request
        branch_origem: Branch com as alterações
        branch_destino: Branch para onde as alterações vão
        
    Returns:
        dict: Informações sobre o pull request criado
    """
    try:
        url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/pulls"
        
        data = {
            "title": titulo,
            "body": descricao,
            "head": branch_origem,
            "base": branch_destino
        }
        
        response = requests.post(url, headers=HEADERS, json=data)
        response.raise_for_status()
        
        pr = response.json()
        
        return {
            "sucesso": True,
            "mensagem": "Pull request criado com sucesso",
            "pull_request": {
                "id": pr.get("id"),
                "numero": pr.get("number"),
                "titulo": pr.get("title"),
                "url": pr.get("html_url"),
                "estado": pr.get("state")
            }
        }
    
    except Exception as e:
        print(f"Erro ao criar pull request: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao criar pull request: {str(e)}"
        }

def criar_branch(
    repo_owner: str,
    repo_name: str,
    nome_branch: str,
    branch_base: str = None
) -> dict:
    """
    Cria uma nova branch no repositório.
    
    Args:
        repo_owner: Nome do proprietário do repositório
        repo_name: Nome do repositório
        nome_branch: Nome da nova branch
        branch_base: Branch da qual a nova branch será criada (opcional, usa a default se não fornecida)
        
    Returns:
        dict: Informações sobre a branch criada
    """
    try:
        # Se branch_base não for fornecida, primeiro descobre a branch padrão
        if not branch_base:
            repo_info_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}"
            repo_response = requests.get(repo_info_url, headers=HEADERS)
            repo_response.raise_for_status()
            branch_base = repo_response.json().get("default_branch", "main")
        
        # Obtém o SHA do commit mais recente da branch base
        ref_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/git/refs/heads/{branch_base}"
        ref_response = requests.get(ref_url, headers=HEADERS)
        ref_response.raise_for_status()
        
        ref_sha = ref_response.json().get("object", {}).get("sha")
        
        # Cria a nova branch
        create_ref_url = f"{API_BASE_URL}/repos/{repo_owner}/{repo_name}/git/refs"
        data = {
            "ref": f"refs/heads/{nome_branch}",
            "sha": ref_sha
        }
        
        response = requests.post(create_ref_url, headers=HEADERS, json=data)
        response.raise_for_status()
        
        return {
            "sucesso": True,
            "mensagem": f"Branch '{nome_branch}' criada com sucesso a partir de '{branch_base}'",
            "branch": {
                "nome": nome_branch,
                "ref": f"refs/heads/{nome_branch}",
                "sha": ref_sha,
                "url": f"https://github.com/{repo_owner}/{repo_name}/tree/{nome_branch}"
            }
        }
    
    except Exception as e:
        print(f"Erro ao criar branch: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao criar branch: {str(e)}"
        }

# Função para testar conexão com a API do GitHub
def testar_conexao() -> dict:
    """
    Testa a conexão com a API do GitHub e verifica se o token é válido.
    
    Returns:
        dict: Informações sobre o usuário autenticado e status da conexão
    """
    try:
        url = f"{API_BASE_URL}/user"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        user = response.json()
        
        return {
            "sucesso": True,
            "mensagem": "Conexão com a API do GitHub estabelecida com sucesso",
            "usuario": {
                "login": user.get("login"),
                "nome": user.get("name"),
                "id": user.get("id"),
                "url": user.get("html_url"),
                "tipo": user.get("type")
            }
        }
    
    except Exception as e:
        print(f"Erro ao testar conexão com a API do GitHub: {str(e)}", file=sys.stderr)
        return {
            "sucesso": False,
            "mensagem": f"Erro ao testar conexão com a API do GitHub: {str(e)}"
        }
