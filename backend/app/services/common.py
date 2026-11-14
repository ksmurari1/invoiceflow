"""Helpers shared by services."""

from app.errors import AppError


def not_found(resource: str) -> AppError:
    """
    Build the 404 error used for missing resources and for other users' resources alike.

    Args:
        resource: Human-readable resource name, e.g. "Client".

    Returns:
        AppError with status 404 and code "not_found".
    """
    return AppError(404, "not_found", f"{resource} not found.")


def escape_like(term: str) -> str:
    """
    Escape LIKE/ILIKE wildcards so user input is matched literally (use with escape="\\").

    Args:
        term: Raw search text.

    Returns:
        Text with backslash, % and _ escaped.
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
