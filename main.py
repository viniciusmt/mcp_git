#!/usr/bin/env python3
"""MCP Git API Server - Versão Simplificada"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Importa o módulo do GitHub
from github_api import (
    listar_repositorios, listar_branches, listar_arquivos,
    obter_conteudo_arquivo, atualizar_arquivo, criar_commit_multiplo,
    criar_pull_request, criar_branch, testar_conexao
)

# Configuração simples
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="MCP Git API", version="1.0.0")

# Headers CORS simples
@app.middleware("http")
async def add_cors(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# Status
@app.get("/")
async def root():
    return {
        "status": "online",
        "name": "MCP Git API",
        "version": "1.0.0",
        "endpoint": "https://mcp-git.onrender.com/mcp"
    }

# Endpoint principal MCP
@app.post("/mcp")
async def handle_mcp(request: Request):
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
                    "capabilities": {"tools": ["gh_testar_conexao", "gh_listar_repositorios", "gh_listar_branches", "gh_listar_arquivos", "gh_obter_conteudo_arquivo", "gh_atualizar_arquivo", "gh_criar_branch", "gh_criar_commit_multiplo", "gh_criar_pull_request"]}
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
