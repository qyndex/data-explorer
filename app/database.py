"""Supabase client for server-side database access.

Uses the service-role key for admin operations (migrations, seed) and the
anon key for user-scoped queries (passed through RLS via the user's JWT).
"""
from __future__ import annotations

import os
from functools import lru_cache

from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client using service-role credentials.

    Env vars required:
      SUPABASE_URL  — e.g. http://localhost:54321
      SUPABASE_SERVICE_ROLE_KEY — from `npx supabase status`
    """
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
            "Run `npx supabase status` to get the values."
        )
    return create_client(url, key)


def get_anon_client() -> Client:
    """Return a Supabase client using the anon key (for RLS-scoped queries).

    Callers typically override the Authorization header with the user's JWT.
    """
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set. "
            "Run `npx supabase status` to get the values."
        )
    return create_client(url, key)
