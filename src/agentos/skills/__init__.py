"""Built-in skills for AgentOS."""

from pathlib import Path
from typing import Optional
import json
import re

from agentos.utils.logger import get_logger

logger = get_logger("agentos.skills")


class SkillsManager:
    """Manages built-in skills for AgentOS.
    
    Loads skills from the skills/ directory and provides
    context for the LLM to use during task execution.
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        """Initialize skills manager.
        
        Args:
            skills_dir: Directory containing skills. Defaults to built-in skills.
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent
        
        self.skills_dir = skills_dir
        self._skills_cache = {}
        self._load_skills_index()
        
    def _load_skills_index(self) -> None:
        """Load index of all available skills."""
        self.skills_index = {}
        
        for category_dir in self.skills_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("."):
                continue
                
            category_name = category_dir.name
            self.skills_index[category_name] = []
            
            for skill_dir in category_dir.iterdir():
                if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                    continue
                    
                skill_path = skill_dir / "SKILL.md"
                if skill_path.exists():
                    # Extract skill name and description from frontmatter
                    content = skill_path.read_text(encoding="utf-8")
                    name = skill_dir.name
                    description = self._extract_description(content)
                    
                    self.skills_index[category_name].append({
                        "name": name,
                        "description": description,
                        "path": str(skill_path),
                    })
                    self._skills_cache[name] = content

        logger.info(f"Loaded {sum(len(v) for v in self.skills_index.values())} skills from {len(self.skills_index)} categories")

    def _extract_description(self, content: str) -> str:
        """Extract description from skill markdown.
        
        Args:
            content: SKILL.md content
            
        Returns:
            First line or description field
        """
        # Try to get from frontmatter description
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            desc_match = re.search(r'description:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
            if desc_match:
                return desc_match.group(1).strip()
        
        # Fallback: first non-empty line
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                return line[:100]
        
        return "No description"

    def list_skills(self, category: Optional[str] = None) -> dict:
        """List available skills.
        
        Args:
            category: Optional category filter
            
        Returns:
            Dictionary of skills/categories
        """
        if category:
            return {category: self.skills_index.get(category, [])}
        return self.skills_index

    def get_skill(self, name: str) -> Optional[str]:
        """Get full skill content.
        
        Args:
            name: Skill name
            
        Returns:
            SKILL.md content or None
        """
        return self._skills_cache.get(name)

    def search_skills(self, query: str) -> list[dict]:
        """Search skills by query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching skills with context
        """
        query_lower = query.lower()
        results = []
        
        for category, skills in self.skills_index.items():
            for skill in skills:
                # Search in name and description
                if (query_lower in skill["name"].lower() or 
                    query_lower in skill["description"].lower()):
                    results.append({
                        **skill,
                        "category": category,
                        "content": self.get_skill(skill["name"]),
                    })
        
        return results

    def get_skills_context(self, task: Optional[str] = None, max_chars: int = 8000) -> str:
        """Get skills context for system prompt.
        
        Builds a context section with available skills
        and relevant skill content for the given task.
        
        Args:
            task: Optional task to match skills against
            max_chars: Maximum characters to include
            
        Returns:
            Formatted skills context
        """
        lines = [
            "\n\n## AVAILABLE SKILLS (92 built-in)",
            "Skills provide specialized knowledge and proven workflows.",
            "Use skill_view(name) to load a skill before performing related tasks.\n",
        ]
        
        # List by category
        for category, skills in sorted(self.skills_index.items()):
            if not skills:
                continue
            lines.append(f"### {category.replace('-', ' ').title()}")
            for skill in skills[:5]:  # First 5 per category
                lines.append(f"- **{skill['name']}**: {skill['description'][:60]}")
            if len(skills) > 5:
                lines.append(f"  ... and {len(skills) - 5} more")
        
        # Add skill search tip
        lines.extend([
            "\n**Usage**: When starting a task, use skills_list() or skills_search()",
            "to find relevant skills, then skill_view(name) to load the full content."
        ])
        
        context = "\n".join(lines)
        
        # Truncate if too long
        if len(context) > max_chars:
            context = context[:max_chars] + f"\n\n... ({len(self._skills_cache)} skills total)"
        
        return context

    def get_total_count(self) -> int:
        """Get total number of skills."""
        return len(self._skills_cache)


# Global instance
_skills_manager: Optional[SkillsManager] = None


def get_skills_manager() -> SkillsManager:
    """Get or create global skills manager."""
    global _skills_manager
    if _skills_manager is None:
        _skills_manager = SkillsManager()
    return _skills_manager
