"""Web tools for AgentOS - search and extract web content."""

import asyncio
from typing import Optional
from agentos.tools.base import BaseTool, ToolResult
from agentos.utils.logger import get_logger

logger = get_logger("agentos.tools.web")


class WebTool(BaseTool):
    """Tool for web operations."""

    def __init__(self):
        super().__init__(
            name="web",
            description="Search the web and extract web content",
            tool_type="custom",
        )
        self._http = None

    async def _get_http(self):
        """Get HTTP client."""
        if self._http is None:
            from agentos.tools.http import HTTPClient
            self._http = HTTPClient()
        return self._http

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> ToolResult:
        """Search the web."""
        try:
            # Use duckduckgo or similar
            url = "https://html.duckduckgo.com/html/"
            data = {"q": query, "b": "", "kl": "us-en"}
            
            http = await self._get_http()
            result = await http.execute(
                url=url,
                method="POST",
                data=f"q={query}",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            
            # Parse results
            import re
            items = []
            matches = re.findall(r'<a class="result__a" href="([^"]*)"[^>]*>([^<]*)</a>', result.output)
            for url, title in matches[:limit]:
                items.append(f"- {title}: {url}")
            
            if not items:
                return ToolResult(
                    success=True,
                    output=f"Search results for '{query}':\n\n{result.output[:1000]}",
                    execution_time=0,
                )
            
            return ToolResult(
                success=True,
                output=f"Search results for '{query}' ({len(items)}):\n" + "\n".join(items),
                execution_time=0,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search error: {e}",
                execution_time=0,
            )

    async def extract(
        self,
        urls: list,
    ) -> ToolResult:
        """Extract content from URLs."""
        try:
            results = []
            http = await self._get_http()
            
            for url in urls[:5]:  # Max 5 URLs
                result = await http.execute(url=url)
                # Get first 2000 chars
                content = result.output[:2000] if result.output else ""
                results.append(f"## {url}\n{content}\n")
            
            return ToolResult(
                success=True,
                output="\n".join(results),
                execution_time=0,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Extract error: {e}",
                execution_time=0,
            )

    async def execute(
        self,
        action: str = "search",
        query: Optional[str] = None,
        urls: Optional[list] = None,
        limit: int = 5,
    ) -> ToolResult:
        """Execute web action."""
        if action == "search":
            return await self.search(query or "", limit)
        elif action == "extract":
            return await self.extract(urls or [])
        else:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                execution_time=0,
            )

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "extract"],
                        "description": "Action to perform",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "URLs to extract",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results",
                    },
                },
                "required": ["action"],
            },
        }