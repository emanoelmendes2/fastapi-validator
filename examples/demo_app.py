"""
Aplicação de demonstração para testar o fastapi-validator.

Esta app contém propositalmente alguns problemas para demonstrar
as capacidades de análise da biblioteca.
"""

from fastapi import FastAPI, Query, Depends
from pydantic import BaseModel

app = FastAPI(title="Demo API", version="1.0.0")


# ============================================
# MODELOS
# ============================================

class User(BaseModel):
    id: int
    name: str
    email: str


class UserCreate(BaseModel):
    name: str
    email: str


# ============================================
# ROTAS COM PROBLEMAS (para demonstração)
# ============================================

# Problema: URL com underscore (deveria ser kebab-case)
@app.get("/user_list")
async def get_user_list():
    """Lista todos os usuários."""
    return []


# Problema: Verbo na URL
@app.get("/get-users")
async def get_users():
    return []


# Problema: Recurso no singular
@app.get("/user/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}


# Problema: POST sem status 201
@app.post("/users")
async def create_user(user: UserCreate):
    return {"id": 1, **user.model_dump()}


# Problema: DELETE sem status 204
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    return {"deleted": True}


# Problema: Sem summary/tags
@app.get("/items")
async def list_items():
    return []


# Problema: Trailing slash
@app.get("/products/")
async def list_products():
    return []


# ============================================
# ROTAS CORRETAS (para comparação)
# ============================================

@app.get(
    "/api/v1/orders",
    summary="List orders",
    tags=["orders"],
    response_model=list[dict],
    status_code=200,
)
async def list_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    """Lista todos os pedidos com paginação."""
    return []


@app.post(
    "/api/v1/orders",
    summary="Create order",
    tags=["orders"],
    status_code=201,
)
async def create_order():
    """Cria um novo pedido."""
    return {"id": 1}


@app.delete(
    "/api/v1/orders/{order_id}",
    summary="Delete order",
    tags=["orders"],
    status_code=204,
)
async def delete_order(order_id: int):
    """Remove um pedido."""
    return None


# ============================================
# APP "BOA" PARA COMPARAÇÃO
# ============================================

good_app = FastAPI(title="Good API", version="1.0.0")


@good_app.get(
    "/api/v1/users",
    summary="List users",
    tags=["users"],
    response_model=list[User],
)
async def good_list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    """Lista usuários com paginação."""
    return []


@good_app.get(
    "/api/v1/users/{user_id}",
    summary="Get user by ID",
    tags=["users"],
    response_model=User,
)
async def good_get_user(user_id: int):
    """Retorna um usuário específico."""
    return User(id=user_id, name="Test", email="test@example.com")


@good_app.post(
    "/api/v1/users",
    summary="Create user",
    tags=["users"],
    response_model=User,
    status_code=201,
)
async def good_create_user(user: UserCreate):
    """Cria um novo usuário."""
    return User(id=1, **user.model_dump())


@good_app.delete(
    "/api/v1/users/{user_id}",
    summary="Delete user",
    tags=["users"],
    status_code=204,
)
async def good_delete_user(user_id: int):
    """Remove um usuário."""
    return None