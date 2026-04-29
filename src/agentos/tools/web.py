"""Web tools for AgentOS - search and extract web content."""

import asyncio
import re
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
        limit: int = 10,
    ) -> ToolResult:
        """Search the web or arxiv."""
        try:
            http = await self._get_http()
            
            # Check if this is an arxiv query
            query_lower = query.lower()
            if "arxiv" in query_lower or "paper" in query_lower:
                # Use arxiv API - clean query first
                # Remove filler words
                clean_q = query
                for word in ['arxiv', 'paper', 'latest', 'recent', 'new', 'find', 'search', 'for', 'about', 'the', 'a', 'an']:
                    clean_q = re.sub(rf'\b{word}\b', '', clean_q, flags=re.IGNORECASE)
                # Clean up extra spaces and +
                clean_q = '+'.join(clean_q.split())
                clean_q = clean_q.strip('+')
                
                if clean_q:
                    url = f"http://export.arxiv.org/api/query?search_query=all:{clean_q}&start=0&max_results={limit}"
                else:
                    url = f"http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results={limit}"
                
                result = await http.execute(url=url)
                
                # Parse arxiv XML response
                entries = re.findall(r'<entry>.*?<title>([^<]+)</title>.*?<summary>([^<]+)</summary>', result.output, re.DOTALL)
                
                if entries:
                    items = []
                    for title, summary in entries[:limit]:
                        items.append(f"- {title[:80]}\n  {summary[:150]}...")
                    return ToolResult(
                        success=True,
                        output=f"arXiv results ({len(items)}):\n" + "\n".join(items),
                        execution_time=0,
                    )
                
                return ToolResult(
                    success=True,
                    output=f"arXiv search: {url}\n\n{result.output[:2000]}",
                    execution_time=0,
                )
            
            # Use DuckDuckGo for regular search
            url = "https://html.duckduckgo.com/html/"
            result = await http.execute(
                url=url,
                method="POST",
                data=f"q={query}",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            
            # Parse results
            matches = re.findall(r'<a class="result__a" href="([^"]*)"[^>]*>([^<]*)</a>', result.output)
            items = []
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