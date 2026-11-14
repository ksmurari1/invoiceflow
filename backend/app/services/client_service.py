"""Client business logic. Every query is scoped by user_id."""

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models.client import Client
from app.models.invoice import Invoice
from app.schemas.client import ClientIn
from app.services.common import escape_like, not_found


def list_clients(
    db: Session, user_id: int, q: str | None, page: int, page_size: int
) -> tuple[list[Client], int]:
    """
    List the user's clients, optionally filtered by a case-insensitive search.

    Args:
        db: Database session
        user_id: Owner of the clients
        q: Search text matched against name, email and company
        page: 1-based page number
        page_size: Items per page

    Returns:
        (clients on this page ordered by name, total matching clients)
    """
    stmt = select(Client).where(Client.user_id == user_id)
    term = (q or "").strip()
    if term:
        pattern = f"%{escape_like(term)}%"
        stmt = stmt.where(
            or_(
                Client.name.ilike(pattern, escape="\\"),
                Client.email.ilike(pattern, escape="\\"),
                Client.company.ilike(pattern, escape="\\"),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(func.lower(Client.name), Client.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), total


def get_client(db: Session, user_id: int, client_id: int, *, for_update: bool = False) -> Client:
    """
    Fetch one of the user's clients.

    Args:
        db: Database session
        user_id: Owner of the client
        client_id: Client id
        for_update: Lock the row for the rest of the transaction

    Returns:
        The client.

    Raises:
        AppError: 404 if it does not exist or belongs to another user.
    """
    stmt = select(Client).where(Client.id == client_id, Client.user_id == user_id)
    if for_update:
        stmt = stmt.with_for_update()
    client = db.scalar(stmt)
    if client is None:
        raise not_found("Client")
    return client


def count_invoices(db: Session, user_id: int, client_id: int) -> int:
    """Return how many invoices (any status) the user has for this client."""
    return (
        db.scalar(
            select(func.count())
            .select_from(Invoice)
            .where(Invoice.user_id == user_id, Invoice.client_id == client_id)
        )
        or 0
    )


def create_client(db: Session, user_id: int, data: ClientIn) -> Client:
    """
    Create a client for the user.

    Args:
        db: Database session
        user_id: Owner of the new client
        data: Validated client fields

    Returns:
        The created client.
    """
    client = Client(user_id=user_id, **data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, user_id: int, client_id: int, data: ClientIn) -> Client:
    """
    Replace a client's fields.

    Args:
        db: Database session
        user_id: Owner of the client
        client_id: Client id
        data: New client fields

    Returns:
        The updated client.
    """
    client = get_client(db, user_id, client_id, for_update=True)
    for field, value in data.model_dump().items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, user_id: int, client_id: int) -> None:
    """
    Delete a client and its draft invoices.

    Args:
        db: Database session
        user_id: Owner of the client
        client_id: Client id

    Raises:
        AppError: 409 if the client has any non-draft invoice (sent, paid or void).
    """
    client = get_client(db, user_id, client_id, for_update=True)
    non_draft = db.scalar(
        select(func.count())
        .select_from(Invoice)
        .where(
            Invoice.user_id == user_id,
            Invoice.client_id == client.id,
            Invoice.status != "draft",
        )
    )
    if non_draft:
        raise AppError(
            409,
            "client_has_invoices",
            "This client has sent, paid or void invoices and cannot be deleted.",
        )
    db.execute(delete(Invoice).where(Invoice.user_id == user_id, Invoice.client_id == client.id))
    db.delete(client)
    db.commit()
