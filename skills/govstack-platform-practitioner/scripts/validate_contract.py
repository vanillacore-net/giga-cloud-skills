#!/usr/bin/env python3
"""Validate minimal portable session/record contracts, never a live platform.

No cloud imports or network calls. The lab owns its full executable session
schema and environment checks. This validator rejects handoff boundary errors.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROLES = {"loadbalancer", "mediator", "examples"}
TARGET_FIELDS = {
    "bootstrap_repo", "environment_config", "inventory", "infrastructure_outputs",
    "image_metadata", "management_context", "clusters", "cluster_configs", "domains", "tls",
}
RECORD_FIELDS = {
    "schema", "case_id", "prior_handoff_reference", "session_reference", "source_revisions",
    "platform_boundary", "management_and_gateway", "clusters", "control_path_evidence",
    "public_edge_to_private_envoy_service_pods", "domains_and_tls", "gitops_ownership_and_revisions",
    "stable_resource_identifiers", "workload_installation_boundary", "use_evidence", "adaptation_evidence",
    "cleanup_or_retention_decision", "cleanup_blockers", "operator_execution", "static_validation",
    "live_validation", "assumptions_and_deviations", "evidence_gaps", "chapter_6_inputs", "review",
    "bounded_next_action",
}
LIST_FIELDS = {
    "control_path_evidence", "public_edge_to_private_envoy_service_pods", "gitops_ownership_and_revisions",
    "stable_resource_identifiers", "use_evidence", "adaptation_evidence", "cleanup_blockers",
    "static_validation", "live_validation", "assumptions_and_deviations", "evidence_gaps", "chapter_6_inputs",
}
LEVELS = {"explained", "prepared", "offline-validated", "live-executed"}
STATUSES = {"passed", "failed", "blocked", "unverified"}
OPERATOR_FIELDS = {
    "kit_source", "operation", "working_directory", "execution_level", "change_approval", "checks",
    "changed_resource_ids", "evidence", "rollback_or_cleanup", "status",
}


def nonempty(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return bool(value) and all(nonempty(v) for v in value)
    return value is not None and value is not False


def role_map(value: object, label: str, errors: list[str], require_values: bool) -> None:
    if not isinstance(value, dict) or set(value) != ROLES:
        errors.append(f"{label}: requires exactly loadbalancer, mediator, examples (two workload spokes)")
    elif require_values:
        for role, target in value.items():
            if not nonempty(target):
                errors.append(f"{label}.{role}: missing target value")


def validate_session(data: object, execute: bool = False) -> list[str]:
    if not isinstance(data, dict):
        return ["session must be a mapping"]
    errors: list[str] = []
    if data.get("schema") != "platform-session/v1":
        errors.append("session schema must be platform-session/v1")
    if not nonempty(data.get("case_id")):
        errors.append("missing case_id")
    for name in TARGET_FIELDS:
        if name not in data or (execute and not nonempty(data[name])):
            errors.append(f"{name}: missing target value")
    for name in ("clusters", "cluster_configs"):
        role_map(data.get(name), name, errors, execute)
    return errors


def validate_record(data: object) -> list[str]:
    if not isinstance(data, dict) or not isinstance(data.get("platform_runtime_record"), dict):
        return ["requires platform_runtime_record mapping"]
    record = data["platform_runtime_record"]
    errors = [f"missing record field {name}" for name in sorted(RECORD_FIELDS - set(record))]
    if record.get("schema") != "platform_runtime_record/v1":
        errors.append("record schema must be platform_runtime_record/v1")
    if not nonempty(record.get("case_id")):
        errors.append("missing case_id")
    role_map(record.get("clusters"), "clusters", errors, False)
    if record.get("workload_installation_boundary") != "chapter-6":
        errors.append("actual workload installation belongs to chapter-6")
    for name in LIST_FIELDS:
        if not isinstance(record.get(name), list):
            errors.append(f"{name}: must be a list")
    for name in ("source_revisions", "management_and_gateway", "domains_and_tls"):
        if not isinstance(record.get(name), dict):
            errors.append(f"{name}: must be a mapping")
    review = record.get("review")
    if not isinstance(review, dict) or set(review) != {"architecture", "content", "syntax", "evidence"}:
        errors.append("review requires four independent axes")
    elif any(v not in {"pass", "needs-work", "unverified"} for v in review.values()):
        errors.append("unknown review verdict")
    operator = record.get("operator_execution")
    if not isinstance(operator, dict):
        return errors + ["operator_execution must be a mapping"]
    errors += [f"missing operator field {name}" for name in sorted(OPERATOR_FIELDS - set(operator))]
    level = operator.get("execution_level")
    if level not in LEVELS:
        errors.append("unknown execution level")
    if operator.get("status") not in STATUSES:
        errors.append("unknown execution status")
    for name in ("checks", "changed_resource_ids", "evidence"):
        if not isinstance(operator.get(name), list):
            errors.append(f"operator_execution.{name}: must be a list")
    if level != "live-executed":
        # Even one live result in a nominally offline record is a contradiction.
        if record.get("live_validation") or operator.get("changed_resource_ids"):
            errors.append("premature live claim: offline level cannot carry live validation or changes")
        for field in ("control_path_evidence", "public_edge_to_private_envoy_service_pods", "use_evidence", "adaptation_evidence"):
            for item in record.get(field, []) if isinstance(record.get(field), list) else []:
                if isinstance(item, dict) and item.get("scope") == "live":
                    errors.append(f"premature live claim in {field}")
        for item in operator.get("evidence", []) if isinstance(operator.get("evidence"), list) else []:
            if isinstance(item, dict) and item.get("scope") == "live":
                errors.append("premature live claim in operator evidence")
    else:
        evidence = operator.get("evidence", [])
        live = [item for item in evidence if isinstance(item, dict) and item.get("scope") == "live"] if isinstance(evidence, list) else []
        if not live or any(not all(nonempty(item.get(k)) for k in ("id", "command", "result", "evidence_reference")) for item in live):
            errors.append("live-executed requires actual live command/result/evidence references")
        if operator.get("changed_resource_ids") and not nonempty(operator.get("change_approval")):
            errors.append("live mutation requires explicit operation approval")
    if record.get("cleanup_blockers") and operator.get("operation") == "cleanup" and operator.get("status") == "passed":
        errors.append("cleanup cannot pass while retirement blockers remain")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("session", "record"))
    parser.add_argument("file", type=Path)
    parser.add_argument("--execute", action="store_true", help="reject missing session target values")
    args = parser.parse_args()
    try:
        data = json.loads(args.file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f"CONTRACT BLOCKED: {exc}\n")
    errors = validate_session(data, args.execute) if args.kind == "session" else validate_record(data)
    if errors:
        parser.exit(1, "CONTRACT BLOCKED:\n" + "\n".join(f"- {e}" for e in errors) + "\n")
    print("CONTRACT PASSED: structural boundary only; no live platform claim")


if __name__ == "__main__":
    main()
