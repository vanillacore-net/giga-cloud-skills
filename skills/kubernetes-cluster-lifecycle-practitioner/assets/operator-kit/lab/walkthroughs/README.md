# Chapter 4 practical walkthroughs

These walkthroughs carry the executable depth behind the chapter. Run them in order. Each step begins with an input state, explains why every inspection or change is needed, and ends with evidence that must exist before the next step.

The tested operator path uses Bash on Linux `amd64`. Windows users run it inside WSL 2; native PowerShell execution is not validated. The reference lab requires a jump host, while an environment with direct private access can adapt the network, inventory and copy steps as one reviewed change.

1. [Discovery](01-discovery.md)
2. [Seed infrastructure](02-seed-infrastructure.md)
3. [Seed cluster rollout](03-seed-cluster.md)
4. [Workload-cluster configuration](04-workload-configuration.md)
5. [Workload-cluster rollout](05-workload-rollout.md)
6. [Adjustments and scaling](06-adjustments.md)
7. [Load-balancer and edge path](07-loadbalancer-edge.md)
8. [Argo CD cluster and workload management](08-argocd-cluster-workload-management.md)
9. [Cleanup](09-cleanup.md)

The examples are safe by default: example contracts are rejected for live use, mutable actions require an explicit kubeconfig and context, and cleanup verifies previously captured stable IDs. They cannot prove that an unknown OpenStack cloud has sufficient capacity or approved routes.
