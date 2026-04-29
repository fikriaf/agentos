"""HTTP client tool for web requests."""

import httpx
import time
from typing import Optional

from agentos.models.tool import ToolType
from agentos.tools.base import BaseTool, ToolResult
from agentos.utils.logger import get_logger

logger = get_logger("agentos.tools.http")


class HTTPClient(BaseTool):
    """Tool for making HTTP requests."""

    def __init__(
        self,
        timeout: int = 30,
        headers: Optional[dict] = None,
    ):
        """Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            headers: Default headers
        """
        super().__init__(
            name="http",
            description="Make HTTP requests. Use for APIs, web scraping, downloading files.",
            tool_type=ToolType.HTTP,
        )
        self.timeout = timeout
        self.default_headers = headers or {}

    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ToolResult:
        """Execute HTTP request.

        Args:
            url: URL to request
            method: HTTP method
            headers: Request headers
            params: Query parameters
            json: JSON body
            data: Raw body
            timeout: Request timeout

        Returns:
            ToolResult
        """
        start_time = time.time()
        timeout = timeout or self.timeout

        merged_headers = {**self.default_headers, **(headers or {})}

        logger.info(f"HTTP {method}: {url}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=merged_headers,
                    params=params,
                    json=json,
                    content=data,
                )

                return ToolResult(
                    success=response.status_code < 400,
                    output=f"Status: {response.status_code}\n\n{response.text[:5000]}",
                    execution_time=time.time() - start_time,
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    },
                )

        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error=f"Request timed out after {timeout}s",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"HTTP error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

    def get_schema(self) -> dict:
        """Get tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to request",
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                        "description": "HTTP method",
                    },
                    "headers": {
                        "type": "object",
                        "description": "Request headers",
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters",
                    },
                    "json": {
                        "type": "object",
                        "description": "JSON body",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                    },
                },
                "required": ["url"],
            },
        }
