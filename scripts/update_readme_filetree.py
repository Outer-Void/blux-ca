"""Update README with generated file tree."""

from __future__ import annotations

from pathlib import Path

from gen_filetree import generate


README_MARKER = "<!-- FILETREE -->"


def update_readme(readme_path: Path = Path("README.md")) -> None:
    content = readme_path.read_text(encoding="utf-8")
    tree = generate()
    snippet = f"{README_MARKER}\n\n````\n{tree}\n````"
    readme_path.write_text(snippet, encoding="utf-8")


if __name__ == "__main__":
    update_readme()
