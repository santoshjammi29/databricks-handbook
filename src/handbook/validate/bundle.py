"""
Databricks Asset Bundle (DAB) Validator.
Parses databricks.yml and all resources/*.yml with PyYAML, validates against the
official Databricks CLI JSON Schema, verifies variable declarations and target modes,
and resolves every referenced notebook, file, and Databricks App path on disk.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import jsonschema
import regex
import yaml
from jsonschema import validators

from handbook.curriculum import EXPECTED_BUNDLE_RESOURCES

VALID_TARGET_MODES: frozenset[str] = frozenset({"development", "production"})
VAR_REF_PATTERN = re.compile(r"\$\{var\.([A-Za-z_][A-Za-z0-9_]*)\}")
EXPR_PATTERN = re.compile(r"\$\{[^}]*(?:\?|==|!=)[^}]*\}")


def _load_bundle_schema(base_dir: Path) -> dict[str, Any]:
    """Loads the committed Databricks CLI JSON Schema from package data."""
    schema_path = base_dir / "src" / "handbook" / "data" / "bundle.schema.json"
    if not schema_path.exists():
        schema_path = Path(__file__).resolve().parent.parent / "data" / "bundle.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _pattern_validator(validator: Any, pat: str, instance: Any, schema_node: dict[str, Any]) -> Any:
    """Regex-backed JSON Schema `pattern` keyword supporting Go Unicode escapes (\\p{L}, \\p{N})."""
    if isinstance(instance, str) and not regex.search(pat, instance):
        yield jsonschema.ValidationError(f"{instance!r} does not match pattern {pat!r}")


def _extract_leaf_errors(err: jsonschema.ValidationError) -> list[jsonschema.ValidationError]:
    """Unwraps nested oneOf/anyOf contexts so error messages point to the root leaf cause."""
    if not err.context:
        return [err]
    leaves: list[jsonschema.ValidationError] = []
    for child in err.context:
        leaves.extend(_extract_leaf_errors(child))
    return leaves


def _deep_merge_resources(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    """Merges `resources` mappings from included resource YAML files."""
    for res_type, res_map in incoming.items():
        if isinstance(res_map, dict) and isinstance(target.get(res_type), dict):
            target[res_type].update(res_map)
        elif isinstance(res_map, dict):
            target[res_type] = dict(res_map)
        else:
            target[res_type] = res_map


def _walk_yaml_strings(node: Any, path: str = "") -> list[tuple[str, str]]:
    """Yields (yaml_path, string_value) pairs from parsed YAML structures."""
    items: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            sub_path = f"{path}.{k}" if path else str(k)
            items.extend(_walk_yaml_strings(v, sub_path))
    elif isinstance(node, list):
        for idx, v in enumerate(node):
            items.extend(_walk_yaml_strings(v, f"{path}[{idx}]"))
    elif isinstance(node, str):
        items.append((path, node))
    return items


def _collect_resource_paths(node: Any, yaml_file: Path, base_dir: Path) -> list[tuple[str, Path]]:
    """Collects (kind, resolved_path) references from a parsed DABs YAML structure."""
    refs: list[tuple[str, Path]] = []

    def _resolve(raw_rel: str) -> Path:
        return (yaml_file.parent / raw_rel).resolve()

    def _walk(cur: Any) -> None:
        if isinstance(cur, dict):
            # notebook_task: { notebook_path: "..." }
            nb_task = cur.get("notebook_task")
            if isinstance(nb_task, dict) and isinstance(nb_task.get("notebook_path"), str):
                refs.append(("notebook_path", _resolve(nb_task["notebook_path"])))

            # spark_python_task: { python_file: "..." }
            py_task = cur.get("spark_python_task")
            if isinstance(py_task, dict) and isinstance(py_task.get("python_file"), str):
                py_file = py_task["python_file"]
                if not py_file.startswith(("dbfs:", "s3:", "abfss:", "gs:", "/Workspace/")):
                    refs.append(("python_file", _resolve(py_file)))

            # DLT libraries: [ { notebook: { path: "..." } }, { file: { path: "..." } } ]
            libs = cur.get("libraries")
            if isinstance(libs, list):
                for lib in libs:
                    if not isinstance(lib, dict):
                        continue
                    nb_entry = lib.get("notebook")
                    if isinstance(nb_entry, dict) and isinstance(nb_entry.get("path"), str):
                        refs.append(("dlt_notebook_path", _resolve(nb_entry["path"])))
                    file_entry = lib.get("file")
                    if isinstance(file_entry, dict) and isinstance(file_entry.get("path"), str):
                        refs.append(("dlt_file_path", _resolve(file_entry["path"])))

            # file_path on dashboards or sql_task.file.path
            if isinstance(cur.get("file_path"), str):
                refs.append(("file_path", _resolve(cur["file_path"])))
            sql_file = cur.get("file")
            if (
                isinstance(sql_file, dict)
                and isinstance(sql_file.get("path"), str)
                and "notebook" not in cur
            ):
                refs.append(("file.path", _resolve(sql_file["path"])))

            # Databricks App source_code_path
            if isinstance(cur.get("source_code_path"), str):
                refs.append(("app_source_code_path", _resolve(cur["source_code_path"])))

            for v in cur.values():
                _walk(v)
        elif isinstance(cur, list):
            for item in cur:
                _walk(item)

    _walk(node)
    return refs


def validate_bundle(base_dir: Path | None = None, verbose: bool = True) -> tuple[bool, list[str]]:
    """
    Validates Databricks Asset Bundle YAML syntax, JSON Schema, target modes,
    variable declarations, and referenced resource paths.
    Returns (success, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    bundle_file = base_dir / "databricks.yml"
    errors: list[str] = []

    if verbose:
        print(f"Validating Databricks Asset Bundle at {base_dir}...")

    if not bundle_file.exists():
        errors.append(f"databricks.yml missing at {bundle_file}")
        return False, errors

    try:
        bundle_data = yaml.safe_load(bundle_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"databricks.yml YAML parse error: {exc}")
        return False, errors

    if not isinstance(bundle_data, dict):
        errors.append("databricks.yml must parse to a YAML mapping")
        return False, errors

    # Required top-level bundle structure
    bundle_meta = bundle_data.get("bundle")
    if not isinstance(bundle_meta, dict) or bundle_meta.get("name") != "databricks-handbook":
        errors.append("databricks.yml must define bundle.name: databricks-handbook")

    targets = bundle_data.get("targets")
    if not isinstance(targets, dict):
        errors.append("databricks.yml must define targets mapping")
    else:
        for req_target in ("dev", "staging", "prod"):
            if req_target not in targets:
                errors.append(f"databricks.yml must define '{req_target}' target")
        for target_name, target_cfg in targets.items():
            if isinstance(target_cfg, dict) and "mode" in target_cfg:
                mode_val = target_cfg["mode"]
                if mode_val not in VALID_TARGET_MODES:
                    errors.append(
                        f"targets.{target_name}.mode: invalid value '{mode_val}' "
                        f"(expected one of {sorted(VALID_TARGET_MODES)})"
                    )

    # Verify expected resource files exist and parse every included resource YAML
    resources_dir = base_dir / "resources"
    for res in EXPECTED_BUNDLE_RESOURCES:
        res_path = resources_dir / res
        if not res_path.exists():
            errors.append(f"Missing resource file {res_path}")

    parsed_files: list[tuple[Path, dict[str, Any]]] = [(bundle_file, bundle_data)]
    merged_bundle: dict[str, Any] = dict(bundle_data)
    merged_resources: dict[str, Any] = {}
    if isinstance(bundle_data.get("resources"), dict):
        _deep_merge_resources(merged_resources, bundle_data["resources"])

    include_patterns = bundle_data.get("include") or []
    included_paths: list[Path] = []
    if isinstance(include_patterns, list):
        for pat in include_patterns:
            if isinstance(pat, str):
                included_paths.extend(sorted(base_dir.glob(pat)))
    # Also ensure every resources/*.yml is validated
    all_resource_files = sorted({*included_paths, *sorted(resources_dir.glob("*.yml"))})

    for yml_file in all_resource_files:
        try:
            yml_data = yaml.safe_load(yml_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{yml_file.name} YAML parse error: {exc}")
            continue
        if yml_data is None:
            yml_data = {}
        if not isinstance(yml_data, dict):
            errors.append(f"{yml_file.name} must parse to a YAML mapping")
            continue
        parsed_files.append((yml_file, yml_data))
        if isinstance(yml_data.get("resources"), dict):
            _deep_merge_resources(merged_resources, yml_data["resources"])

    if merged_resources:
        merged_bundle["resources"] = merged_resources

    # Check declared variables and disallow unsupported ternary/comparison expressions
    declared_vars = set((bundle_data.get("variables") or {}).keys())
    for yml_file, data in parsed_files:
        rel_name = yml_file.relative_to(base_dir)
        for yaml_path, s_val in _walk_yaml_strings(data):
            if EXPR_PATTERN.search(s_val):
                errors.append(f"{rel_name} ({yaml_path}): unsupported DABs expression '{s_val}'")
            for var_name in VAR_REF_PATTERN.findall(s_val):
                if var_name not in declared_vars:
                    errors.append(
                        f"{rel_name} ({yaml_path}): undeclared variable '${{var.{var_name}}}'"
                    )

    # Validate merged bundle against Databricks CLI JSON Schema
    try:
        schema = _load_bundle_schema(base_dir)
        base_validator = validators.validator_for(schema)
        custom_validator_cls = validators.extend(
            base_validator, validators={"pattern": _pattern_validator}
        )
        validator = custom_validator_cls(schema)
        for schema_err in validator.iter_errors(merged_bundle):
            leaves = _extract_leaf_errors(schema_err)
            # Deduplicate identical leaf messages while keeping concise context
            seen_msgs: set[str] = set()
            for leaf in leaves:
                loc = ".".join(str(p) for p in leaf.path) or "<root>"
                msg = f"bundle schema error at {loc}: {leaf.message}"
                if msg not in seen_msgs:
                    seen_msgs.add(msg)
                    errors.append(msg)
    except Exception as exc:  # pragma: no cover - schema load failure guard
        errors.append(f"Failed to execute Databricks bundle JSON Schema validation: {exc}")

    # Resolve all referenced notebook, file, and app source paths
    resolved_paths: list[Path] = []
    for yml_file, data in parsed_files:
        rel_name = yml_file.relative_to(base_dir)
        for kind, target_path in _collect_resource_paths(data, yml_file, base_dir):
            if not target_path.exists():
                try:
                    disp = target_path.relative_to(base_dir)
                except ValueError:
                    disp = target_path
                errors.append(f"{rel_name} references non-existent {kind}: {disp}")
                continue
            resolved_paths.append(target_path)
            if kind == "app_source_code_path":
                for required_app_file in ("app.py", "app.yaml", "requirements.txt"):
                    if not (target_path / required_app_file).exists():
                        errors.append(
                            f"Missing {required_app_file} in Databricks App {target_path}"
                        )

    # Enforce explicit app presence even if apps.yml is mutated
    app_dir = base_dir / "apps" / "lakehouse_finops_monitor"
    for required_app_file in ("app.py", "app.yaml", "requirements.txt"):
        if not (app_dir / required_app_file).exists():
            errors.append(f"Missing {required_app_file} in Databricks App")

    if verbose:
        if errors:
            print("\n--- BUNDLE INTEGRITY ERRORS DETECTED ---")
            for err in errors:
                print(f"  ❌ {err}")
        else:
            print(
                f"✅ Databricks Asset Bundle verified: parsed + schema-validated + "
                f"{len(resolved_paths)} resource paths resolved!"
            )

    return len(errors) == 0, errors


def main() -> None:
    success, _ = validate_bundle()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
