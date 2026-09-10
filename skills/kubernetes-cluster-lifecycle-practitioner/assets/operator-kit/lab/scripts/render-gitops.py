#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml


def main() -> int:
    p = argparse.ArgumentParser(description="Render Argo CD project, cluster-lifecycle Application and workload ApplicationSet")
    p.add_argument("--repo-url", required=True)
    p.add_argument("--revision", required=True)
    p.add_argument("--cluster-path", default="clusters")
    p.add_argument("--workload-path", default="workloads/demo")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--allow-example", action="store_true")
    a = p.parse_args()
    if a.repo_url.startswith("https://example.invalid") and not a.allow_example:
        print("ERROR: replace the example repository URL", file=sys.stderr)
        return 2
    if any(v.startswith("/") or ".." in Path(v).parts for v in (a.cluster_path, a.workload_path)):
        print("ERROR: repository paths must be relative and cannot contain '..'", file=sys.stderr)
        return 2

    project = {
        "apiVersion": "argoproj.io/v1alpha1", "kind": "AppProject",
        "metadata": {"name": "chapter-4-platform", "namespace": "argocd"},
        "spec": {
            "description": "Chapter 4 cluster lifecycle and bounded workload delivery",
            "sourceRepos": [a.repo_url],
            "destinations": [
                {"server": "https://kubernetes.default.svc", "namespace": "*"},
                {"server": "*", "namespace": "workload-demo"},
            ],
            "clusterResourceWhitelist": [{"group": "cluster.x-k8s.io", "kind": "ClusterClass"}],
            "namespaceResourceWhitelist": [{"group": "*", "kind": "*"}],
            "namespaceResourceBlacklist": [{"group": "", "kind": "Secret"}],
        },
    }
    lifecycle = {
        "apiVersion": "argoproj.io/v1alpha1", "kind": "Application",
        "metadata": {"name": "child-cluster-lifecycle", "namespace": "argocd"},
        "spec": {
            "project": "chapter-4-platform",
            "source": {"repoURL": a.repo_url, "targetRevision": a.revision, "path": a.cluster_path},
            "destination": {"server": "https://kubernetes.default.svc", "namespace": "default"},
            "syncPolicy": {"automated": {"prune": False, "selfHeal": True}, "syncOptions": ["ServerSideApply=true"]},
        },
    }
    workloads = {
        "apiVersion": "argoproj.io/v1alpha1", "kind": "ApplicationSet",
        "metadata": {"name": "registered-workload-clusters", "namespace": "argocd"},
        "spec": {
            "goTemplate": True,
            "goTemplateOptions": ["missingkey=error"],
            "generators": [{"clusters": {"selector": {"matchLabels": {"platform.vanillacore.net/workloads-enabled": "true"}}}}],
            "template": {
                "metadata": {"name": "{{.name}}-workload-demo"},
                "spec": {
                    "project": "chapter-4-platform",
                    "source": {"repoURL": a.repo_url, "targetRevision": a.revision, "path": a.workload_path},
                    "destination": {"server": "{{.server}}", "namespace": "workload-demo"},
                    "syncPolicy": {"automated": {"prune": True, "selfHeal": True}},
                },
            },
        },
    }
    a.output.mkdir(parents=True, exist_ok=True)
    for name, obj in (("01-project.yaml", project), ("02-cluster-lifecycle.yaml", lifecycle), ("03-workloads-applicationset.yaml", workloads)):
        (a.output / name).write_text(yaml.safe_dump(obj, sort_keys=False))
    print(f"Rendered 3 Argo CD declarations to {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
