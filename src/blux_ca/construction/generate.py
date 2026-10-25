"""Deterministic content: strict templates and canonical configuration files.

Templates use `${name}` placeholders (Python `string.Template`). Substitution is strict both ways: a
placeholder without a parameter and a parameter without a placeholder are both errors, so a typo cannot
silently produce a file. `$$` writes a literal `$`.

Configuration formats and their canonical output:

| format | input | output |
|---|---|---|
| json | any JSON value | 2-space indent, sorted keys, UTF-8, final newline |
| toml | object; no nulls | scalars and arrays first, then tables and arrays of tables, keys sorted |
| yaml | any JSON value | block style, keys sorted, every string double-quoted |
| ini | {section: {key: scalar}} | `[section]` blocks, `key = value`, sorted |
| env | {KEY: scalar} | `KEY="value"`, sorted; `\\`, `"`, `$` and `` ` `` escaped |

JSON and TOML output is parsed back and compared with the input before it is accepted; INI output is
re-read with `configparser`.
"""

from __future__ import annotations

import configparser
import json
import re
import string
import tomllib
from typing import Any

from blux_ca.construction.common import CaError

BUILTIN_TEMPLATES: dict[str, str] = {
    "python.module": '"""${summary}"""\n',
    "python.package": '"""${summary}"""\n\n__version__ = "${version}"\n',
    "python.test": (
        '"""Tests for ${module}."""\n\nfrom ${module} import ${name}\n\n\n'
        "def test_${name}_is_callable() -> None:\n    assert callable(${name})\n"
    ),
    "markdown.readme": "# ${title}\n\n${summary}\n",
    "gitignore.python": "__pycache__/\n*.py[cod]\n.venv/\nbuild/\ndist/\n*.egg-info/\n.pytest_cache/\n",
    "editorconfig": (
        "root = true\n\n[*]\ncharset = utf-8\nend_of_line = lf\ninsert_final_newline = true\n"
        "trim_trailing_whitespace = true\n"
    ),
}
FORMATS = ("json", "toml", "yaml", "ini", "env")
EXTENSIONS = {
    ".json": "json",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".ini": "ini",
    ".cfg": "ini",
    ".env": "env",
}
BARE_KEY = re.compile(r"^[A-Za-z0-9_-]+$")
ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def render(template: str, params: dict[str, str], where: str) -> str:
    tpl = string.Template(template)
    if not tpl.is_valid():
        raise CaError("TEMPLATE_ERROR", f"{where}: the template has an invalid placeholder.", {"where": where})
    wanted = set(tpl.get_identifiers())
    missing, unused = sorted(wanted - set(params)), sorted(set(params) - wanted)
    if missing or unused:
        raise CaError(
            "TEMPLATE_ERROR",
            f"{where}: missing parameters {missing}, unused parameters {unused}.",
            {"where": where, "missing": missing, "unused": unused},
        )
    return tpl.substitute(params)


def builtin(name: str, params: dict[str, str], where: str) -> str:
    if name not in BUILTIN_TEMPLATES:
        raise CaError("TEMPLATE_ERROR", f"{where}: no built-in template {name!r}.", {"where": where})
    return render(BUILTIN_TEMPLATES[name], params, where)


def format_for(path: str, declared: str | None) -> str:
    suffix = "." + path.rsplit(".", 1)[-1] if "." in path.rsplit("/", 1)[-1] else ""
    inferred = EXTENSIONS.get(suffix.lower()) or ("env" if path.rsplit("/", 1)[-1].startswith(".env") else None)
    if declared is None:
        if inferred is None:
            raise CaError("INVALID_REQUEST", f"Cannot infer a config format from {path!r}; give `format`.")
        return inferred
    if inferred is not None and inferred != declared:
        raise CaError(
            "CONFLICTING_INSTRUCTIONS", f"{path!r} looks like {inferred}, but format is {declared}.", {"path": path}
        )
    return declared


def config(fmt: str, data: Any, where: str) -> str:
    try:
        text = {"json": _json, "toml": _toml, "yaml": _yaml, "ini": _ini, "env": _env}[fmt](data)
    except CaError as exc:
        raise CaError(exc.code, f"{where}: {exc.message}", {"where": where, **exc.details}) from None
    return text


def _json(data: Any) -> str:
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    if json.loads(text) != data:  # pragma: no cover - json round-trips its own output
        raise CaError("CONFIG_ERROR", "JSON output does not round-trip.")
    return text


def _scalar_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def _toml_key(key: str) -> str:
    return key if BARE_KEY.match(key) else _scalar_json(key)


def _toml_value(value: Any) -> str:
    if value is None:
        raise CaError("CONFIG_ERROR", "TOML has no null value.")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return _scalar_json(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{_toml_key(k)} = {_toml_value(v)}" for k, v in sorted(value.items())) + "}"
    raise CaError("CONFIG_ERROR", f"Cannot write {type(value).__name__} as TOML.")  # pragma: no cover


def _is_table_array(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(v, dict) for v in value)


def _toml_table(data: dict[str, Any], prefix: list[str], out: list[str]) -> None:
    simple = [(k, v) for k, v in sorted(data.items()) if not isinstance(v, dict) and not _is_table_array(v)]
    for key, value in simple:
        out.append(f"{_toml_key(key)} = {_toml_value(value)}\n")
    for key, value in sorted(data.items()):
        path = [*prefix, _toml_key(key)]
        if isinstance(value, dict):
            out.append(f"\n[{'.'.join(path)}]\n")
            _toml_table(value, path, out)
        elif _is_table_array(value):
            for item in value:
                out.append(f"\n[[{'.'.join(path)}]]\n")
                _toml_table(item, path, out)


def _toml(data: Any) -> str:
    if not isinstance(data, dict):
        raise CaError("CONFIG_ERROR", "A TOML document must be an object.")
    out: list[str] = []
    _toml_table(data, [], out)
    text = "".join(out).lstrip("\n")
    try:
        reread = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise CaError("CONFIG_ERROR", f"Cannot be written as TOML: {exc}.") from None
    if reread != data:
        raise CaError("CONFIG_ERROR", "TOML output does not round-trip (mixed int/float types?).")
    return text


def _yaml_node(value: Any, indent: str, out: list[str]) -> None:
    if isinstance(value, dict) and value:
        for key, child in sorted(value.items()):
            if isinstance(child, (dict, list)) and child:
                out.append(f"{indent}{_scalar_json(key)}:\n")
                _yaml_node(child, indent + "  ", out)
            else:
                out.append(f"{indent}{_scalar_json(key)}: {_yaml_scalar(child)}\n")
    elif isinstance(value, list) and value:
        for child in value:
            if isinstance(child, (dict, list)) and child:
                out.append(f"{indent}-\n")
                _yaml_node(child, indent + "  ", out)
            else:
                out.append(f"{indent}- {_yaml_scalar(child)}\n")
    else:
        out.append(f"{indent}{_yaml_scalar(value)}\n")


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value == {}:
        return "{}"
    if value == []:
        return "[]"
    if isinstance(value, bool):
        return "true" if value else "false"
    return _scalar_json(value)


def _yaml(data: Any) -> str:
    out: list[str] = []
    _yaml_node(data, "", out)
    return "".join(out)


def _ini_scalar(value: Any, where: str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _scalar_json(value)
    if isinstance(value, str):
        if "\n" in value or "\r" in value or value != value.strip():
            raise CaError("CONFIG_ERROR", f"INI value for {where} has a newline or surrounding spaces.")
        return value
    raise CaError("CONFIG_ERROR", f"INI value for {where} must be a string, number or boolean.")


def _ini(data: Any) -> str:
    if not isinstance(data, dict) or not all(isinstance(v, dict) for v in data.values()):
        raise CaError("CONFIG_ERROR", "An INI document must be {section: {key: value}}.")
    out: list[str] = []
    for section, values in sorted(data.items()):
        if not section or any(c in section for c in "[]\n\r"):
            raise CaError("CONFIG_ERROR", f"Invalid INI section name {section!r}.")
        out.append(f"[{section}]\n")
        for key, value in sorted(values.items()):
            if not key or key != key.strip() or any(c in key for c in "=:\n\r[;#"):
                raise CaError("CONFIG_ERROR", f"Invalid INI key {key!r}.")
            out.append(f"{key} = {_ini_scalar(value, f'{section}.{key}')}\n")
        out.append("\n")
    text = "".join(out).rstrip("\n") + "\n" if out else ""
    parser = configparser.ConfigParser(interpolation=None, delimiters=("=",), comment_prefixes=("#", ";"))
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    parser.read_string(text)
    reread = {s: dict(parser[s]) for s in parser.sections()}
    if reread != {s: {k: _ini_scalar(v, k) for k, v in vals.items()} for s, vals in data.items()}:
        raise CaError("CONFIG_ERROR", "INI output does not round-trip.")  # pragma: no cover
    return text


def _env(data: Any) -> str:
    if not isinstance(data, dict):
        raise CaError("CONFIG_ERROR", "An env document must be an object of KEY: value.")
    out = []
    for key, value in sorted(data.items()):
        if not ENV_KEY.match(key):
            raise CaError("CONFIG_ERROR", f"Invalid environment variable name {key!r}.")
        text = _ini_scalar(value, key) if not isinstance(value, str) else value
        if "\n" in text or "\r" in text:
            raise CaError("CONFIG_ERROR", f"Value of {key} has a newline.")
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")
        out.append(f'{key}="{escaped}"\n')
    return "".join(out)
