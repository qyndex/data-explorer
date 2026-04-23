"""Routes for saved queries and query results."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.models import (
    QueryResultListResponse,
    QueryResultResponse,
    SavedQueryCreate,
    SavedQueryListResponse,
    SavedQueryResponse,
)
from app.services import shared_data_service as data_service

router = APIRouter(tags=["queries"])


# ---------------------------------------------------------------------------
# Saved queries
# ---------------------------------------------------------------------------


@router.get("/queries", response_model=SavedQueryListResponse)
async def list_queries(user_id: str = Depends(get_current_user_id)):
    """List all saved queries for the authenticated user."""
    queries = data_service.list_queries(user_id)
    return {"queries": queries}


@router.post(
    "/queries",
    response_model=SavedQueryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_query(
    body: SavedQueryCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Save a new query."""
    result = data_service.save_query(
        owner_id=user_id,
        dataset_id=body.dataset_id,
        name=body.name,
        sql_query=body.sql_query,
        description=body.description,
    )
    return result


@router.get("/queries/{query_id}", response_model=SavedQueryResponse)
async def get_query(
    query_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a single saved query."""
    query = data_service.get_query(query_id, user_id)
    if query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return query


@router.delete("/queries/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_query(
    query_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a saved query."""
    data_service.delete_query(query_id, user_id)


# ---------------------------------------------------------------------------
# Query results (execute + history)
# ---------------------------------------------------------------------------


@router.post(
    "/queries/{query_id}/execute",
    response_model=QueryResultResponse,
    status_code=status.HTTP_201_CREATED,
)
async def execute_query(
    query_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Execute a saved query and cache the result."""
    result = data_service.execute_and_store_query(query_id, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Query or dataset not found")
    return result


@router.get(
    "/queries/{query_id}/results",
    response_model=QueryResultListResponse,
)
async def list_query_results(
    query_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """List cached results for a query."""
    results = data_service.list_query_results(query_id, user_id)
    return {"results": results}
