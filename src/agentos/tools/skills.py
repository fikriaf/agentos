"""Skills tool for AgentOS."""

import asyncio
from typing import Optional
from agentos.tools.base import BaseTool, ToolResult
from agentos.utils.logger import get_logger

logger = get_logger("agentos.tools.skills")


class SkillsTool(BaseTool):
    """Tool for interacting with skills."""

    def __init__(self):
        super().__init__(
            name="skills",
            description="Manage and query skills - list, search, view skills",
            tool_type="custom",
        )

    async def list_skills(self, category: Optional[str] = None) -> ToolResult:
        """List available skills."""
        from agentos.skills import SkillsManager
        mgr = SkillsManager()
        skills = mgr.list_skills(category)
        
        lines = []
        count = 0
        # skills is a dict: {category: [{name, description, path}, ...]}
        if isinstance(skills, dict):
            for cat, cat_skills in skills.items():
                for s in cat_skills:
                    if isinstance(s, dict):
                        name = s.get('name', 'unknown')
                        desc = s.get('description', '')[:60]
                    else:
                        name = str(s)
                        desc = ""
                    lines.append(f"- {name}: {desc}")
                    count += 1
        else:
            lines.append(f"Unknown format: {skills}")
        
        return ToolResult(
            success=True,
            output=f"Available skills ({count}):\n" + "\n".join(lines[:50]),
            execution_time=0,
        )

    async def search_skills(self, query: str) -> ToolResult:
        """Search skills by query."""
        from agentos.skills import SkillsManager
        mgr = SkillsManager()
        results = mgr.search_skills(query)
        
        lines = []
        # Handle different return formats safely
        if isinstance(results, dict):
            for name, desc in results.items():
                lines.append(f"- {name}: {desc}")
        elif isinstance(results, list):
            for item in results:
                if isinstance(item, tuple) and len(item) >= 2:
                    lines.append(f"- {item[0]}: {item[1]}")
                elif isinstance(item, dict):
                    lines.append(f"- {item.get('name', 'unknown')}: {item.get('description', '')[:50]}")
                else:
                    lines.append(f"- {item}")
        
        if not lines:
            return ToolResult(
                success=True,
                output=f"Found 0 matches:\n\nQuery: {query}",
                execution_time=0,
            )
        
        return ToolResult(
            success=True,
            output=f"Search results for '{query}' ({len(results)}):\n" + "\n".join(lines[:30]),
            execution_time=0,
        )

    async def view_skill(self, name: str, file_path: Optional[str] = None) -> ToolResult:
        """View a specific skill."""
        from agentos.skills import SkillsManager
        mgr = SkillsManager()
        
        try:
            if file_path:
                content = mgr.get_skill(name, file_path)
            else:
                content = mgr.get_skill(name)
            if content:
                if file_path:
                    return ToolResult(
                        success=True,
                        output=f"Loaded {name}/{file_path}:\n\n{content[:5000]}",
                        execution_time=0,
                    )
                else:
                    return ToolResult(
                        success=True,
                        output=f"Skill: {name}\n\n{content[:5000]}",
                        execution_time=0,
                    )
            else:
                return ToolResult(
                    success=False,
                    error=f"Skill '{name}' not found",
                    execution_time=0,
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Skill '{name}' error: {e}",
                execution_time=0,
            )

    async def execute(
        self,
        action: str = "list",
        query: Optional[str] = None,
        name: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> ToolResult:
        """Execute skills action."""
        if action == "list":
            return await self.list_skills(query)
        elif action == "search":
            return await self.search_skills(query or "")
        elif action == "view":
            return await self.view_skill(name or "", file_path)
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
                        "enum": ["list", "search", "view"],
                        "description": "Action to perform",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "name": {
                        "type": "string",
                        "description": "Skill name",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "File path within skill",
                    },
                },
                "required": ["action"],
            },
        }