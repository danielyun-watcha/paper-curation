"""Shared HTTP client utilities for connection pooling and reuse"""
from __future__ import annotations

from typing import Optional
import httpx


class HttpClientManager:
    """
    Manages shared httpx.AsyncClient instances for connection pooling.
    Provides separate clients for different services to allow custom configurations.
    """

    _clients: dict[str, httpx.AsyncClient] = {}
    _default_timeout = 30.0

    @classmethod
    def get_client(
        cls,
        name: str = "default",
        timeout: float = None,
        headers: Optional[dict] = None,
    ) -> httpx.AsyncClient:
        """
        Get or create a shared AsyncClient instance.

        Args:
            name: Client identifier (e.g., "semantic_scholar", "arxiv")
            timeout: Request timeout in seconds
            headers: Default headers for all requests

        Returns:
            Shared AsyncClient instance
        """
        if name not in cls._clients:
            cls._clients[name] = httpx.AsyncClient(
                timeout=timeout or cls._default_timeout,
                headers=headers or {},
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return cls._clients[name]

    @classmethod
    async def close_all(cls):
        """Close all managed clients (call on app shutdown)"""
        for client in cls._clients.values():
            await client.aclose()
        cls._clients.clear()

    @classmethod
    async def close_client(cls, name: str):
        """Close a specific client"""
        if name in cls._clients:
            await cls._clients[name].aclose()
            del cls._clients[name]


def get_http_client(name: str = "default", timeout: float = 30.0) -> httpx.AsyncClient:
    """
    Convenience function to get a shared HTTP client.

    Args:
        name: Client identifier
        timeout: Request timeout

    Returns:
        Shared AsyncClient instance
    """
    return HttpClientManager.get_client(name, timeout)
