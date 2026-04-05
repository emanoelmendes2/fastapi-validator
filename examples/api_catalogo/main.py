"""
API de Catálogo de Produtos - API B para testes de validação.

Uma API simulada representando um sistema de catálogo de produtos
em estágio inicial de desenvolvimento, com violações moderadas
de boas práticas RESTful.
"""

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

app = FastAPI(
    title="API Catálogo de Produtos",
    description="API para gerenciamento de catálogo de produtos",
    version="1.0.0",
)


# ============================================================
# Models
# ============================================================

class ProdutoCreate(BaseModel):
    nome: str
    descricao: str
    preco: float
    categoria_id: int
    estoque: int = 0


class ProdutoResponse(BaseModel):
    id: int
    nome: str
    descricao: str
    preco: float
    categoria_id: int
    estoque: int
    criado_em: datetime


class CategoriaCreate(BaseModel):
    nome: str
    descricao: str


class CategoriaResponse(BaseModel):
    id: int
    nome: str
    descricao: str


class AvaliacaoCreate(BaseModel):
    produto_id: int
    nota: int
    comentario: str


class AvaliacaoResponse(BaseModel):
    id: int
    produto_id: int
    nota: int
    comentario: str
    criado_em: datetime


# ============================================================
# Dados simulados
# ============================================================

produtos_db: list[dict] = []
categorias_db: list[dict] = []
avaliacoes_db: list[dict] = []


# ============================================================
# Endpoints de Produtos — com violações intencionais
# ============================================================

# Violação: URL com underscore (deveria ser kebab-case)
# Violação: verbo na URL (get)
# Violação: sem tags
@app.get("/get_produtos")
def get_produtos(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Retorna lista de produtos."""
    return produtos_db


# Violação: sem summary/description
# Violação: sem tags
@app.get("/produtos/{produto_id}")
def get_produto(produto_id: int):
    return {"produto_id": produto_id}


# Violação: POST retornando 200 (deveria ser 201)
# Violação: sem response_model
# Violação: sem tags
@app.post("/produtos")
def create_produto(produto: ProdutoCreate):
    novo = {"id": len(produtos_db) + 1, **produto.model_dump(), "criado_em": datetime.now()}
    produtos_db.append(novo)
    return novo


# Violação: sem summary/description
# Violação: sem response_model
@app.put("/produtos/{produto_id}")
def update_produto(produto_id: int, produto: ProdutoCreate):
    return {"id": produto_id, **produto.model_dump()}


# Violação: DELETE retornando 200 (deveria ser 204)
# Violação: sem tags
@app.delete("/produtos/{produto_id}")
def delete_produto(produto_id: int):
    return {"message": "Produto removido"}


# Violação: verbo na URL (search)
# Violação: underscore na URL
@app.get("/produtos/search_by_name")
def search_by_name(q: str = Query(...)):
    """Busca produtos por nome."""
    return [p for p in produtos_db if q.lower() in p["nome"].lower()]


# ============================================================
# Endpoints de Categorias — com algumas violações
# ============================================================

# Violação: recurso no singular (deveria ser /categorias)
# Violação: sem description
@app.get(
    "/categoria",
    summary="Listar categorias",
    tags=["categorias"],
)
def listar_categorias():
    return categorias_db


# Violação: POST retornando 200
@app.post(
    "/categoria",
    summary="Criar categoria",
    tags=["categorias"],
)
def criar_categoria(categoria: CategoriaCreate):
    nova = {"id": len(categorias_db) + 1, **categoria.model_dump()}
    categorias_db.append(nova)
    return nova


@app.get(
    "/categoria/{categoria_id}",
    summary="Buscar categoria por ID",
    tags=["categorias"],
)
def buscar_categoria(categoria_id: int):
    return {"categoria_id": categoria_id}


@app.delete(
    "/categoria/{categoria_id}",
    summary="Remover categoria",
    tags=["categorias"],
)
def remover_categoria(categoria_id: int):
    return {"message": "Categoria removida"}


# ============================================================
# Endpoints de Avaliações — mistura de bom e ruim
# ============================================================

# Violação: trailing slash
# Violação: sem tags
@app.get("/avaliacoes/")
def listar_avaliacoes():
    """Lista todas as avaliações."""
    return avaliacoes_db


# Violação: sem tags, sem summary
# Violação: POST retornando 200
@app.post("/avaliacoes")
def criar_avaliacao(avaliacao: AvaliacaoCreate):
    nova = {"id": len(avaliacoes_db) + 1, **avaliacao.model_dump(), "criado_em": datetime.now()}
    avaliacoes_db.append(nova)
    return nova


# Violação: URL com verbo e underscore
@app.get("/avaliacoes/get_by_produto/{produto_id}")
def get_avaliacoes_by_produto(produto_id: int):
    """Busca avaliações de um produto específico."""
    return [a for a in avaliacoes_db if a["produto_id"] == produto_id]


# ============================================================
# Endpoint de saúde — bem implementado
# ============================================================

@app.get(
    "/health",
    summary="Health check",
    description="Verifica se a API está funcionando corretamente.",
    tags=["sistema"],
    response_model=dict,
)
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ============================================================
# Endpoint com dado sensível na URL — violação de segurança
# ============================================================

# Violação: dado sensível (token) na URL
@app.get("/usuarios/{user_id}/token/{token}")
def verificar_token(user_id: int, token: str):
    """Verifica token do usuário."""
    return {"valid": True}
