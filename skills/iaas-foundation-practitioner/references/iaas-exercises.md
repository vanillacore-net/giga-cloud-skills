# Chapter 3 learner exercises

Use one exercise at a time. In challenge exercises, capture the learner's answer before giving corrections.

## 1. Capability before product

**Task:** Map identity, administrative boundary, image, compute, network policy, external address, persistent storage, quota, and placement to their jobs. Then map the same capabilities to OpenStack services.

**Pass conditions:**

- Keystone, Glance, Nova with Placement, Neutron, and Cinder follow generic capabilities.
- Horizon, OpenStackClient, and OpenTofu are interfaces, not extra infrastructure layers.
- Quota and physical capacity remain separate.

## 2. Resource-chain challenge

**Scenario:** A server is `ACTIVE`, a floating IP is allocated, and a volume is `in-use`. The learner claims the service is reachable and durable.

**Task:** Name the exact relationships and states still required.

**Pass conditions:** The answer asks for server-to-port, port-to-security-group, floating-IP-to-port, and volume-attachment-to-server relationships by stable ID. It also keeps DNS, TLS, login, filesystem, application, backup, and recovery outside the proved IaaS result.

## 3. Discovery ledger

**Task:** Classify each proposed value as supplied, discovered, approved, reference example, or unknown: cloud profile, project ID, region, image ID, flavor, VM network, external network, ingress CIDR, compute availability zone, volume availability zone, volume type, and service-specific quotas.

**Pass conditions:** No example value becomes a live input. Compute and block-storage zones remain separate. Quota evidence does not become capacity evidence.

## 4. Interface-path review

**Task:** Choose Horizon, OpenStackClient, or OpenTofu. Write a complete fresh-session path with prerequisites, requested result, state changes, read-back, failure states, and cleanup.

**Pass conditions:** One interface owns creation. Any handoff carries the cloud profile and stable identifiers explicitly. Expected results are predicates, not fabricated transcripts.

## 5. Cleanup ordering

**Task:** Order approval, identifier capture, floating-IP release, server or interface removal, volume detach, server deletion, security-group deletion, optional volume deletion, and absence checks.

**Pass conditions:** Persistent data has an explicit retain or delete decision. Every wait is bounded and stops on terminal error. Absence is proved by captured ID. A retained volume is `available` and unattached.

## Feedback format

Return:

```yaml
assessment:
  architecture: pass | needs_revision | not_assessed
  content: pass | needs_revision | not_assessed
  syntax: pass | needs_revision | unverified
  evidence: pass | needs_revision | unverified
  unsupported_claims: []
  missing_relationships: []
  repair_order: []
  next_exercise:
```
