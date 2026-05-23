"""Parse a query string into a Query object.

Query syntax:  FIELD:OPERATOR:VALUE [AND FIELD:OPERATOR:VALUE ...] [LIMIT N]

Examples:
    message:contains:ERROR
    level:eq:WARN AND message:regex:timeout LIMIT 50
    raw:contains:404 AND status:gt:399
"""

import re
from typing import Optional

from logslice.query import Query, QueryCondition

_CONDITION_RE = re.compile(r"(\w+):(\w+):(.+?)(?=\s+AND\s+|\s+LIMIT\s+|$)", re.IGNORECASE)
_LIMIT_RE = re.compile(r"LIMIT\s+(\d+)", re.IGNORECASE)


class QueryParseError(ValueError):
    """Raised when a query string cannot be parsed."""


def parse_query(query_str: str) -> Query:
    """Parse a query string and return a Query object.

    Args:
        query_str: Human-readable query expression.

    Returns:
        Query instance ready to apply against log entries.

    Raises:
        QueryParseError: If the query string is malformed.
    """
    query_str = query_str.strip()
    if not query_str:
        return Query()

    limit: Optional[int] = None
    limit_match = _LIMIT_RE.search(query_str)
    if limit_match:
        limit = int(limit_match.group(1))
        query_str = query_str[: limit_match.start()].strip()

    conditions = []
    for match in _CONDITION_RE.finditer(query_str):
        field_name, operator, value = match.group(1), match.group(2), match.group(3).strip()
        try:
            conditions.append(QueryCondition(field=field_name, operator=operator, value=value))
        except ValueError as exc:
            raise QueryParseError(str(exc)) from exc

    if not conditions and query_str:
        raise QueryParseError(f"No valid conditions found in query: '{query_str}'")

    return Query(conditions=conditions, limit=limit)
