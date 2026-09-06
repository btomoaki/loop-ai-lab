from pathlib import Path
from typing import Any


class TemplateManager:
    """
    Centralized template manager for loading and rendering prompt templates from template/prompt/.
    Eliminates hardcoded prompt strings in Python codebase.
    """
    _template_dir: Path = Path(__file__).resolve().parent.parent.parent / "template" / "prompt"

    @classmethod
    def set_template_dir(cls, template_dir: Path) -> None:
        cls._template_dir = template_dir

    @classmethod
    def get_template_path(cls, template_path_rel: str) -> Path:
        return cls._template_dir / template_path_rel

    @classmethod
    def render(cls, template_path_rel: str, **kwargs: Any) -> str:
        """
        Loads the template file from template/prompt/ and formats it using kwargs.
        Raises FileNotFoundError if template does not exist.
        """
        tpl_path = cls.get_template_path(template_path_rel)
        if not tpl_path.exists():
            raise FileNotFoundError(f"❌ [TemplateManager Error] Template file not found: {tpl_path}")
        
        tpl_content = tpl_path.read_text(encoding="utf-8")
        try:
            rendered = tpl_content.format(**kwargs)
        except KeyError as e:
            raise RuntimeError(
                f"❌ [TemplateManager Error] Missing format key '{e.args[0]}' in template '{template_path_rel}'. "
                f"Provided keys: {list(kwargs.keys())}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"❌ [TemplateManager Error] Failed to format template '{template_path_rel}': {e}. "
                f"Provided keys: {list(kwargs.keys())}"
            ) from e

        if not rendered or not rendered.strip():
            raise RuntimeError(f"❌ [TemplateManager Error] Rendered prompt for '{template_path_rel}' resulted in empty string!")

        return rendered
