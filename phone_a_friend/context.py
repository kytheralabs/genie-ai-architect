"""Collect project context for AI prompts.

ProjectContext gathers code, SQL, schemas, notebooks, and free-form text
into a single markdown document suitable for prepending to an AI call.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProjectContext:
    project_name: str
    sections: list[tuple[str, str]] = field(default_factory=list)

    def add_code(self, code: str, label: str = "Code") -> "ProjectContext":
        self.sections.append((label, f"```python\n{code.strip()}\n```"))
        return self

    def add_sql(self, sql: str, label: str = "SQL") -> "ProjectContext":
        self.sections.append((label, f"```sql\n{sql.strip()}\n```"))
        return self

    def add_text(self, text: str, label: str = "Notes") -> "ProjectContext":
        self.sections.append((label, text.strip()))
        return self

    def add_schema(self, schema_text: str, label: str = "Schema") -> "ProjectContext":
        self.sections.append((label, f"```text\n{schema_text.strip()}\n```"))
        return self

    def add_table_metadata(self, metadata: str, label: str = "Table Metadata") -> "ProjectContext":
        self.sections.append((label, f"```text\n{metadata.strip()}\n```"))
        return self

    def add_directory(
        self,
        path,
        pattern: str = "*.py",
        label_relative_to=None,
        skip_empty: bool = True,
    ) -> "ProjectContext":
        """Recursively load files matching *pattern* from *path*.

        Extension determines how each file is added:
        ``.py`` \u2192 add_code(); ``.md`` / ``.toml`` / ``.txt`` \u2192 add_text().
        The label is the path relative to *label_relative_to* (defaults to *path*).
        Empty files are skipped when *skip_empty* is True.
        """
        from pathlib import Path

        _TEXT_EXTS = {".md", ".toml", ".txt", ".yaml", ".yml"}
        root = Path(path)
        base = Path(label_relative_to) if label_relative_to else root
        for file_path in sorted(root.rglob(pattern)):
            source = file_path.read_text()
            if skip_empty and not source.strip():
                continue
            label = str(file_path.relative_to(base))
            if file_path.suffix in _TEXT_EXTS:
                self.add_text(source, label=label)
            else:
                self.add_code(source, label=label)
        return self

    def add_notebook_file(self, path, label: str | None = None) -> "ProjectContext":
        """Extract code cells from a Jupyter notebook (.ipynb) and add as code.

        All non-empty code cells are joined and added as a single add_code() call
        labelled by the notebook stem (or *label* if provided).
        """
        import json
        from pathlib import Path

        nb_path = Path(path)
        nb_label = label or nb_path.stem
        nb = json.loads(nb_path.read_text())
        sources = []
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                src = "".join(cell.get("source", []))
                if src.strip():
                    sources.append(src)
        if sources:
            self.add_code("\n\n# --- next cell ---\n\n".join(sources), label=nb_label)
        return self

    def add_workspace_notebook(self, path, label: str | None = None) -> "ProjectContext":
        """Export a Databricks workspace notebook and add its code cells as code.

        *path* is the workspace path (e.g. /Users/me/my-notebook).
        Uses SOURCE format (Python source, no outputs) to avoid the 10 MB JUPYTER
        export limit.  Cells are split on ``# COMMAND ----------``; markdown cells
        are skipped; ``# MAGIC`` prefixes are stripped from other magic cells.
        """
        import base64

        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.workspace import ExportFormat

        nb_label = label or path.split("/")[-1]
        w = WorkspaceClient()
        export = w.workspace.export(path=path, format=ExportFormat.SOURCE)
        raw = base64.b64decode(export.content).decode("utf-8")

        sources = []
        for chunk in raw.split("# COMMAND ----------"):
            chunk = chunk.strip()
            if not chunk or "Databricks notebook source" in chunk:
                continue
            # Skip markdown cells
            first_line = next((ln for ln in chunk.splitlines() if ln.strip()), "")
            if "# MAGIC %md" in first_line:
                continue
            # Strip MAGIC prefixes (sql, sh, run, etc.)
            cleaned = "\n".join(
                ln[len("# MAGIC "):] if ln.startswith("# MAGIC ") else ln
                for ln in chunk.splitlines()
            ).strip()
            if cleaned:
                sources.append(cleaned)

        if sources:
            self.add_code("\n\n# --- next cell ---\n\n".join(sources), label=nb_label)
        return self

    def render(self) -> str:
        lines = [f"# Project Context: {self.project_name}"]
        for title, content in self.sections:
            lines.append(f"## {title}")
            lines.append(content)
        return "\n\n".join(lines).strip()
