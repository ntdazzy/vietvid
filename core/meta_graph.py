"""Client dùng chung cho mọi provider gọi Meta/Instagram Graph API.

Gom phần lặp giữa các provider Meta/IG (dispatch video, đọc comment, trả lời
comment): giữ ``access_token`` + ``graph_version`` + ``httpx`` client, và 1 CHỖ
DUY NHẤT dựng base URL ``graph.facebook.com``. Provider Meta/IG kế thừa thêm
class này (đa kế thừa cùng base nghiệp vụ) để khỏi lặp init + URL pattern.
"""

from __future__ import annotations

import httpx


class MetaGraphClient:
    def __init__(
        self,
        access_token: str,
        graph_version: str,
        *,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.access_token = access_token
        self.graph_version = graph_version
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout)

    def graph_url(self, path: str) -> str:
        return f"https://graph.facebook.com/{self.graph_version}/{path}"

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
