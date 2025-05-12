#!/usr/bin/env python3
"""MCP Git API Server - Com endpoints HTTP diretos"""

import os
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

# Importa o módulo do GitHub
from github_api import (
    listar_repositorios, listar_branches, listar_arquivos,
    obter_conteudo_arquivo, atualizar_arquivo, criar_commit_multiplo,
    criar_pull_request, criar_branch, testar_conexao
)

# Configuração simples
logging.basicConfig(level=logging.INFO)
app = FastAPI(
    title="MCP Git API", 
    version="1.0.0",
    servers=[{"url": "https://mcp-git.onrender.com", "description": "Production server"}]
)

# Models para endpoints REST (sem duplicar parâmetros da URL)
class FileData(BaseModel):
    conteudo: str
    mensagem_commit: str
    branch: Optional[str] = None
    sha: Optional[str] = None

class BranchData(BaseModel):
    nome_branch: str
    branch_base: Optional[str] = None

class MultiCommitData(BaseModel):
    mensagem_commit: str
    alteracoes: List[Dict[str, str]]
    branch: Optional[str] = None

class PullRequestData(BaseModel):
    titulo: str
    descricao: str
    branch_origem: str
    branch_destino: str

# OpenAPI customizado
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="MCP Git API",
        version="1.0.0",
        description="API for GitHub integration via MCP protocol and REST endpoints",
        routes=app.routes,
    )
    
    openapi_schema["servers"] = [
        {"url": "https://mcp-git.onrender.com", "description": "Production server"}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Headers CORS
@app.middleware("http")
async def add_cors(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# === ENDPOINTS HTTP DIRETOS ===

# Testar conexão
@app.get("/test-connection", tags=["GitHub"])
async def test_github_connection():
    """🔗 Testa conexão com a API do GitHub"""
    return testar_conexao()

# Listar repositórios
@app.get("/repositories", tags=["GitHub"])
async def list_repositories(username: Optional[str] = None):
    """📚 Lista repositórios do usuário ou organização"""
    return listar_repositorios(username)

# Listar branches
@app.get("/repositories/{repo_owner}/{repo_name}/branches", tags=["GitHub"])
async def list_branches(repo_owner: str, repo_name: str):
    """🌿 Lista branches de um repositório"""
    result = listar_branches(repo_owner, repo_name)
    if not result.get("sucesso"):
        raise HTTPException(status_code=404, detail=result.get("mensagem"))
    return result

# Listar arquivos
@app.get("/repositories/{repo_owner}/{repo_name}/contents", tags=["GitHub"])
async def list_files(repo_owner: str, repo_name: str, path: str = "", branch: Optional[str] = None):
    """📁 Lista arquivos e diretórios de um repositório"""
    result = listar_arquivos(repo_owner, repo_name, path, branch)
    if not result.get("sucesso"):
        raise HTTPException(status_code=404, detail=result.get("mensagem"))
    return result

# Obter arquivo
@app.get("/repositories/{repo_owner}/{repo_name}/contents/{path:path}", tags=["GitHub"])
async def get_file(repo_owner: str, repo_name: str, path: str, branch: Optional[str] = None):
    """📖 Obtém conteúdo de um arquivo específico"""
    result = obter_conteudo_arquivo(repo_owner, repo_name, path, branch)
    if not result.get("sucesso"):
        raise HTTPException(status_code=404, detail=result.get("mensagem"))
    return result

# Criar/atualizar arquivo
@app.post("/repositories/{repo_owner}/{repo_name}/contents/{path:path}", tags=["GitHub"])
async def create_or_update_file(repo_owner: str, repo_name: str, path: str, data: FileData):
    """✏️ Cria ou atualiza um arquivo no repositório"""
    result = atualizar_arquivo(
        repo_owner, repo_name, path, 
        data.conteudo, data.mensagem_commit, 
        data.branch, data.sha
    )
    if not result.get("sucesso"):
        raise HTTPException(status_code=400, detail=result.get("mensagem"))
    return result

# Criar branch
@app.post("/repositories/{repo_owner}/{repo_name}/branches", tags=["GitHub"])
async def create_branch(repo_owner: str, repo_name: str, data: BranchData):
    """🔀 Cria uma nova branch no repositório"""
    result = criar_branch(repo_owner, repo_name, data.nome_branch, data.branch_base)
    if not result.get("sucesso"):
        raise HTTPException(status_code=400, detail=result.get("mensagem"))
    return result

# Commit múltiplo
@app.post("/repositories/{repo_owner}/{repo_name}/commits", tags=["GitHub"])
async def create_multi_commit(repo_owner: str, repo_name: str, data: MultiCommitData):
    """📦 Cria um commit com múltiplos arquivos"""
    result = criar_commit_multiplo(
        repo_owner, repo_name, 
        data.mensagem_commit, data.alteracoes, 
        data.branch
    )
    if not result.get("sucesso"):
        raise HTTPException(status_code=400, detail=result.get("mensagem"))
    return result

# Criar pull request
@app.post("/repositories/{repo_owner}/{repo_name}/pulls", tags=["GitHub"])
async def create_pull_request(repo_owner: str, repo_name: str, data: PullRequestData):
    """🔄 Cria um pull request no repositório"""
    result = criar_pull_request(
        repo_owner, repo_name, data.titulo, data.descricao,
        data.branch_origem, data.branch_destino
    )
    if not result.get("sucesso"):
        raise HTTPException(status_code=400, detail=result.get("mensagem"))
    return result

# === ENDPOINTS MCP (mantidos) ===

# Status
@app.get("/")
async def root():
    return {
        "status": "online",
        "name": "MCP Git API",
        "version": "1.0.0",
        "protocols": ["REST", "MCP"],
        "rest_endpoints": {
            "test_connection": "/test-connection",
            "repositories": "/repositories",
            "branches": "/repositories/{owner}/{repo}/branches",
            "files": "/repositories/{owner}/{repo}/contents",
            "create_file": "POST /repositories/{owner}/{repo}/contents/{path}",
            "create_branch": "POST /repositories/{owner}/{repo}/branches",
            "create_commit": "POST /repositories/{owner}/{repo}/commits",
            "create_pr": "POST /repositories/{owner}/{repo}/pulls"
        },
        "mcp_endpoint": "/mcp"
    }

# OpenAPI endpoint
@app.get("/.well-known/openapi.json")
def get_openapi_json():
    return custom_openapi()

# Endpoint MCP (mantido para compatibilidade)
@app.post("/mcp", tags=["MCP"])
async def handle_mcp(request: Request):
    """🔄 Endpoint MCP para operações via JSON-RPC"""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id", "unknown")
        
        if method == "invoke":
            tool_method = params.get("method")
            arguments = params.get("arguments", {})
            
            # Mapeia métodos para funções
            methods_map = {
                "gh_testar_conexao": lambda: testar_conexao(),
                "gh_listar_repositorios": lambda: listar_repositorios(arguments.get("username")),
                "gh_listar_branches": lambda: listar_branches(arguments.get("repo_owner"), arguments.get("repo_name")),
                "gh_listar_arquivos": lambda: listar_arquivos(arguments.get("repo_owner"), arguments.get("repo_name"), arguments.get("path", ""), arguments.get("branch")),
                "gh_obter_conteudo_arquivo": lambda: obter_conteudo_arquivo(arguments.get("repo_owner"), arguments.get("repo_name"), arguments.get("path"), arguments.get("branch")),
                "gh_atualizar_arquivo": lambda: atualizar_arquivo(arguments.get("repo_owner"), arguments.get("repo_name"), arguments.get("path"), arguments.get("conteudo"), arguments.get("mensagem_commit"), arguments.get("branch"), arguments.get("sha")),
                "gh_criar_branch": lambda: criar_branch(arguments.get("repo_owner"), arguments.get("repo_name"), arguments.get("nome_branch"), arguments.get("branch_base")),
                "gh_criar_commit_multiplo": lambda: criar_commit_multiplo(arguments.get("repo_owner"), arguments.get("repo_name"), arguments.get("mensagem_commit"), arguments.get("alteracoes", []), arguments.get("branch")),
                "gh_criar_pull_request": lambda: criar_pull_request(arguments.get("repo_owner"), arguments.get("repo_name"), arguments.get("titulo"), arguments.get("descricao"), arguments.get("branch_origem"), arguments.get("branch_destino"))
            }
            
            if tool_method in methods_map:
                result = methods_map[tool_method]()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Método não encontrado: {tool_method}"}
                }
        
        elif method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "serverInfo": {"name": "MCP Git API", "version": "1.0.0"},
                    "capabilities": {
                        "tools": {
                            "gh_testar_conexao": {"description": "Test GitHub connection"},
                            "gh_listar_repositorios": {"description": "List repositories"},  
                            "gh_listar_branches": {"description": "List branches"},
                            "gh_listar_arquivos": {"description": "List files"},
                            "gh_obter_conteudo_arquivo": {"description": "Get file content"},
                            "gh_atualizar_arquivo": {"description": "Create/update file"},
                            "gh_criar_branch": {"description": "Create branch"},
                            "gh_criar_commit_multiplo": {"description": "Multi-file commit"},
                            "gh_criar_pull_request": {"description": "Create pull request"}
                        }
                    }
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Método MCP não encontrado: {method}"}
            }
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": "unknown",
                "error": {"code": -32603, "message": f"Erro interno: {str(e)}"}
            }
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
