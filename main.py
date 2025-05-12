#!/usr/bin/env python3
"""
MCP Git API Server
Exposição das funcionalidades do GitHub via FastAPI com suporte ao protocolo MCP
"""

import os
import sys
import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import uvicorn

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importa o módulo do GitHub
from github_api import (
    listar_repositorios,
    listar_branches,
    listar_arquivos,
    obter_conteudo_arquivo,
    atualizar_arquivo,
    excluir_arquivo,
    criar_commit_multiplo,
    criar_pull_request,
    criar_branch,
    testar_conexao
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    logger.info("Iniciando MCP Git API Server...")
    # Testa conexão com GitHub na inicialização
    result = testar_conexao()
    if result.get("sucesso"):
        logger.info(f"Conectado ao GitHub como: {result['usuario']['login']}")
    else:
        logger.warning(f"Falha na conexão com GitHub: {result.get('mensagem')}")
    
    yield  # Aplicação roda aqui
    
    logger.info("Finalizando MCP Git API Server...")

# Inicializa FastAPI com lifespan
app = FastAPI(
    title="MCP Git API",
    description="API para integração GitHub via protocolo MCP",
    version="1.0.0",
    lifespan=lifespan,
    servers=[
        {
            "url": "https://mcp-git.onrender.com",
            "description": "Production server"
        },
        {
            "url": "http://localhost:10000",
            "description": "Development server"
        }
    ]
)

def get_custom_openapi():
    """Gera especificação OpenAPI customizada para MCP"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="MCP Git API",
        version="1.0.0",
        description="API para integração GitHub via protocolo MCP",
        routes=app.routes,
    )
    
    # Adiciona informações específicas do MCP
    openapi_schema["info"]["x-mcp-version"] = "2024-11-05"
    openapi_schema["info"]["x-mcp-protocol"] = True
    
    # Configura os servidores corretamente
    openapi_schema["servers"] = [
        {
            "url": "https://mcp-git.onrender.com",
            "description": "Production server"
        },
        {
            "url": "http://localhost:10000",
            "description": "Development server"
        }
    ]
    
    # Adiciona configurações específicas do MCP
    openapi_schema["info"]["x-mcp-server"] = {
        "name": "MCP Git API",
        "version": "1.0.0",
        "protocol": "mcp"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Rota principal para status
@app.get("/", tags=["Status"])
async def root():
    """Endpoint de status da API"""
    return {
        "status": "online",
        "name": "MCP Git API",
        "version": "1.0.0",
        "protocol": "MCP",
        "server": "https://mcp-git.onrender.com",
        "endpoints": {
            "mcp": "/mcp",
            "openapi": "/.well-known/openapi.json"
        }
    }

# Rota para obter especificação OpenAPI
@app.get("/.well-known/openapi.json")
def mcp_openapi():
    """Rota para a especificação OpenAPI no formato exigido pelo MCP."""
    return get_custom_openapi()

# Rota para lidar com requisições MCP
@app.post("/mcp", tags=["MCP"])
async def handle_mcp(request: Request):
    """Manipula requisições no formato MCP (Model Control Protocol)"""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id", "unknown")
        
        logger.info(f"Recebida requisição MCP: método={method}, id={request_id}")
        
        if method == "invoke":
            tool_method = params.get("method")
            arguments = params.get("arguments", {})
            
            # Listar repositórios
            if tool_method == "gh_listar_repositorios":
                username = arguments.get("username")
                result = listar_repositorios(username)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Listar branches
            elif tool_method == "gh_listar_branches":
                repo_owner = arguments.get("repo_owner")
                repo_name = arguments.get("repo_name")
                if not repo_owner or not repo_name:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "repo_owner e repo_name são obrigatórios"}
                    }
                result = listar_branches(repo_owner, repo_name)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Listar arquivos
            elif tool_method == "gh_listar_arquivos":
                repo_owner = arguments.get("repo_owner")
                repo_name = arguments.get("repo_name")
                path = arguments.get("path", "")
                branch = arguments.get("branch")
                if not repo_owner or not repo_name:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "repo_owner e repo_name são obrigatórios"}
                    }
                result = listar_arquivos(repo_owner, repo_name, path, branch)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Obter conteúdo de arquivo
            elif tool_method == "gh_obter_conteudo_arquivo":
                repo_owner = arguments.get("repo_owner")
                repo_name = arguments.get("repo_name")
                path = arguments.get("path")
                branch = arguments.get("branch")
                if not repo_owner or not repo_name or not path:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "repo_owner, repo_name e path são obrigatórios"}
                    }
                result = obter_conteudo_arquivo(repo_owner, repo_name, path, branch)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Atualizar/criar arquivo
            elif tool_method == "gh_atualizar_arquivo":
                repo_owner = arguments.get("repo_owner")
                repo_name = arguments.get("repo_name")
                path = arguments.get("path")
                conteudo = arguments.get("conteudo")
                mensagem_commit = arguments.get("mensagem_commit")
                branch = arguments.get("branch")
                sha = arguments.get("sha")
                
                if not all([repo_owner, repo_name, path, conteudo, mensagem_commit]):
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "repo_owner, repo_name, path, conteudo e mensagem_commit são obrigatórios"}
                    }
                
                result = atualizar_arquivo(repo_owner, repo_name, path, conteudo, mensagem_commit, branch, sha)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Criar branch
            elif tool_method == "gh_criar_branch":
                repo_owner = arguments.get("repo_owner")
                repo_name = arguments.get("repo_name")
                nome_branch = arguments.get("nome_branch")
                branch_base = arguments.get("branch_base")
                
                if not all([repo_owner, repo_name, nome_branch]):
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "repo_owner, repo_name e nome_branch são obrigatórios"}
                    }
                
                result = criar_branch(repo_owner, repo_name, nome_branch, branch_base)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Criar commit múltiplo
            elif tool_method == "gh_criar_commit_multiplo":
                repo_owner = arguments.get("repo_owner")
                repo_name = arguments.get("repo_name")
                mensagem_commit = arguments.get("mensagem_commit")
                alteracoes = arguments.get("alteracoes", [])
                branch = arguments.get("branch")
                
                if not all([repo_owner, repo_name, mensagem_commit, alteracoes]):
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "repo_owner, repo_name, mensagem_commit e alteracoes são obrigatórios"}
                    }
                
                result = criar_commit_multiplo(repo_owner, repo_name, mensagem_commit, alteracoes, branch)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Criar pull request
            elif tool_method == "gh_criar_pull_request":
                repo_owner = arguments.get("repo_owner")
                repo_name = arguments.get("repo_name")
                titulo = arguments.get("titulo")
                descricao = arguments.get("descricao")
                branch_origem = arguments.get("branch_origem")
                branch_destino = arguments.get("branch_destino")
                
                if not all([repo_owner, repo_name, titulo, descricao, branch_origem, branch_destino]):
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "Todos os campos são obrigatórios para criar um PR"}
                    }
                
                result = criar_pull_request(repo_owner, repo_name, titulo, descricao, branch_origem, branch_destino)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            # Testar conexão
            elif tool_method == "gh_testar_conexao":
                result = testar_conexao()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            else:
                logger.warning(f"Método MCP desconhecido: {tool_method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Método não encontrado: {tool_method}"}
                }
        
        elif method == "initialize":
            # Retorna as capacidades do servidor
            capabilities = {
                "tools": {
                    "gh_listar_repositorios": {
                        "description": "Lista todos os repositórios do usuário ou organização",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "username": {
                                    "type": "string",
                                    "description": "Nome do usuário ou organização (opcional)"
                                }
                            }
                        }
                    },
                    "gh_listar_branches": {
                        "description": "Lista todas as branches de um repositório",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "repo_owner": {"type": "string", "description": "Proprietário do repositório"},
                                "repo_name": {"type": "string", "description": "Nome do repositório"}
                            },
                            "required": ["repo_owner", "repo_name"]
                        }
                    },
                    "gh_listar_arquivos": {
                        "description": "Lista arquivos e diretórios em um repositório",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "repo_owner": {"type": "string", "description": "Proprietário do repositório"},
                                "repo_name": {"type": "string", "description": "Nome do repositório"},
                                "path": {"type": "string", "description": "Caminho para listar (opcional)"},
                                "branch": {"type": "string", "description": "Branch (opcional)"}
                            },
                            "required": ["repo_owner", "repo_name"]
                        }
                    },
                    "gh_obter_conteudo_arquivo": {
                        "description": "Obtém o conteúdo de um arquivo específico",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "repo_owner": {"type": "string", "description": "Proprietário do repositório"},
                                "repo_name": {"type": "string", "description": "Nome do repositório"},
                                "path": {"type": "string", "description": "Caminho do arquivo"},
                                "branch": {"type": "string", "description": "Branch (opcional)"}
                            },
                            "required": ["repo_owner", "repo_name", "path"]
                        }
                    },
                    "gh_atualizar_arquivo": {
                        "description": "Atualiza ou cria um arquivo no repositório",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "repo_owner": {"type": "string", "description": "Proprietário do repositório"},
                                "repo_name": {"type": "string", "description": "Nome do repositório"},
                                "path": {"type": "string", "description": "Caminho do arquivo"},
                                "conteudo": {"type": "string", "description": "Conteúdo do arquivo"},
                                "mensagem_commit": {"type": "string", "description": "Mensagem do commit"},
                                "branch": {"type": "string", "description": "Branch (opcional)"},
                                "sha": {"type": "string", "description": "SHA do arquivo (para atualização)"}
                            },
                            "required": ["repo_owner", "repo_name", "path", "conteudo", "mensagem_commit"]
                        }
                    },
                    "gh_criar_branch": {
                        "description": "Cria uma nova branch no repositório",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "repo_owner": {"type": "string", "description": "Proprietário do repositório"},
                                "repo_name": {"type": "string", "description": "Nome do repositório"},
                                "nome_branch": {"type": "string", "description": "Nome da nova branch"},
                                "branch_base": {"type": "string", "description": "Branch base (opcional)"}
                            },
                            "required": ["repo_owner", "repo_name", "nome_branch"]
                        }
                    },
                    "gh_criar_commit_multiplo": {
                        "description": "Cria um commit com múltiplas alterações",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "repo_owner": {"type": "string", "description": "Proprietário do repositório"},
                                "repo_name": {"type": "string", "description": "Nome do repositório"},
                                "mensagem_commit": {"type": "string", "description": "Mensagem do commit"},
                                "alteracoes": {
                                    "type": "array",
                                    "description": "Lista de alterações",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "path": {"type": "string"},
                                            "conteudo": {"type": "string"}
                                        }
                                    }
                                },
                                "branch": {"type": "string", "description": "Branch (opcional)"}
                            },
                            "required": ["repo_owner", "repo_name", "mensagem_commit", "alteracoes"]
                        }
                    },
                    "gh_criar_pull_request": {
                        "description": "Cria um pull request no repositório",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "repo_owner": {"type": "string", "description": "Proprietário do repositório"},
                                "repo_name": {"type": "string", "description": "Nome do repositório"},
                                "titulo": {"type": "string", "description": "Título do PR"},
                                "descricao": {"type": "string", "description": "Descrição do PR"},
                                "branch_origem": {"type": "string", "description": "Branch origem"},
                                "branch_destino": {"type": "string", "description": "Branch destino"}
                            },
                            "required": ["repo_owner", "repo_name", "titulo", "descricao", "branch_origem", "branch_destino"]
                        }
                    },
                    "gh_testar_conexao": {
                        "description": "Testa a conexão com a API do GitHub",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
            }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "serverInfo": {
                        "name": "MCP Git API",
                        "version": "1.0.0"
                    },
                    "capabilities": capabilities
                }
            }
        
        else:
            logger.warning(f"Método MCP desconhecido: {method}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Método MCP não encontrado: {method}"}
            }
            
    except Exception as e:
        logger.exception(f"Exceção ao processar requisição MCP: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": "unknown",
                "error": {"code": -32603, "message": f"Erro interno: {str(e)}"}
            }
        )

# Sobrescreve a função openapi padrão do FastAPI
app.openapi = get_custom_openapi

# Função para inicializar o servidor
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Iniciando servidor na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)