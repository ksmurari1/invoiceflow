"""Client endpoints: /api/v1/clients."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientDetailOut, ClientIn, ClientOut
from app.schemas.common import ErrorResponse, Page
from app.services import client_service

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)


def _detail(db: Session, user: User, client: Client) -> ClientDetailOut:
    count = client_service.count_invoices(db, user.id, client.id)
    return ClientDetailOut.model_validate(
        {**ClientOut.model_validate(client).model_dump(), "invoice_count": count}
    )


@router.get("", response_model=Page[ClientOut])
async def list_clients(
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[ClientOut]:
    """List the current user's clients (search by name, email or company)."""
    clients, total = client_service.list_clients(db, user.id, q, page, page_size)
    return Page[ClientOut](
        items=[ClientOut.model_validate(c) for c in clients],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ClientDetailOut, status_code=201)
async def create_client(
    data: ClientIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ClientDetailOut:
    """Create a client."""
    client = client_service.create_client(db, user.id, data)
    return _detail(db, user, client)


@router.get("/{client_id}", response_model=ClientDetailOut)
async def read_client(
    client_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ClientDetailOut:
    """Get one client with its invoice count."""
    return _detail(db, user, client_service.get_client(db, user.id, client_id))


@router.put("/{client_id}", response_model=ClientDetailOut)
async def update_client(
    client_id: int,
    data: ClientIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ClientDetailOut:
    """Replace a client's fields."""
    client = client_service.update_client(db, user.id, client_id, data)
    return _detail(db, user, client)


@router.delete(
    "/{client_id}",
    status_code=204,
    response_class=Response,
    responses={409: {"model": ErrorResponse}},
)
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Delete a client and its drafts (409 if it has sent, paid or void invoices)."""
    client_service.delete_client(db, user.id, client_id)
    return Response(status_code=204)
