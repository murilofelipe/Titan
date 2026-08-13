import os
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ContextItem(BaseModel):
    """Represents a single loaded context file and its metadata."""
    file_path: str
    content: Optional[str] = None
    exists: bool = True
    error: Optional[str] = None


class LoadedStepContext(BaseModel):
    """Container for all loaded context items associated with a pipeline step."""
    step_name: str = ""
    items: Dict[str, ContextItem] = Field(default_factory=dict)

    def is_empty(self) -> bool:
        """Returns True if no context items are loaded."""
        return len(self.items) == 0


def load_context_file(file_path: str, base_dir: str = ".") -> ContextItem:
    """Loads a single context file from disk.

    Args:
        file_path: Relative or absolute path to the context file.
        base_dir: Base directory to resolve relative paths against.

    Returns:
        ContextItem containing the file content or error information.
    """
    resolved_path = file_path if os.path.isabs(file_path) else os.path.join(base_dir, file_path)

    if not os.path.exists(resolved_path):
        return ContextItem(file_path=file_path, exists=False, error=f"File not found: {file_path}")

    if not os.path.isfile(resolved_path):
        return ContextItem(file_path=file_path, exists=False, error=f"Path is not a file: {file_path}")

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ContextItem(file_path=file_path, content=content, exists=True)
    except Exception as e:
        return ContextItem(file_path=file_path, exists=False, error=f"Error reading file: {e}")


def load_step_context(context_files: List[str], base_dir: str = ".", step_name: str = "") -> LoadedStepContext:
    """Loads all specified context files for a pipeline step.

    Args:
        context_files: List of context file paths.
        base_dir: Base directory to resolve relative paths against.
        step_name: Optional name of the step.

    Returns:
        LoadedStepContext mapping file paths to ContextItem instances.
    """
    items: Dict[str, ContextItem] = {}
    for fp in context_files:
        items[fp] = load_context_file(fp, base_dir=base_dir)
    return LoadedStepContext(step_name=step_name, items=items)


def format_context_for_prompt(loaded_context: LoadedStepContext) -> str:
    """Formats loaded context items into a markdown string block for agent prompts or display.

    Args:
        loaded_context: The LoadedStepContext to format.

    Returns:
        Formatted markdown string or empty string if context is empty.
    """
    if loaded_context.is_empty():
        return ""

    blocks = ["### 📂 Contexto Injetado Automático"]
    for path, item in loaded_context.items.items():
        if item.exists and item.content is not None:
            blocks.append(f"#### Arquivo: `{path}`\n```markdown\n{item.content}\n```")
        else:
            blocks.append(f"⚠️ **Aviso ({path})**: {item.error or 'Conteúdo indisponível'}")

    return "\n\n".join(blocks)
