---
name: cloud-decision-matrix-steward
description: Maintain one evidence-based public-service hosting matrix.
version: 0.1.0
metadata:
  hermes:
    tags: [cloud, hosting, decision-matrix, evidence, public-sector]
---
# Cloud decision matrix steward

Use when several contributors or companion skills have produced service facts, option comparisons and evidence gaps that must become one reviewable local decision matrix. It maintains a shared frame. It does not make a local choice.

## Input

```yaml
service_context:
  purpose:
  current_hosting:
  option_families:
assessment_inputs:
  workload_facts:
  accountability_and_control:
  sovereignty_requirements:
  interoperability_and_dependencies:
  operating_capacity_and_cost:
  portability_and_exit:
```

## Procedure

1. Use one shared criterion set: service criticality and continuity; data and records; demand, performance and connectivity; integration; accountability and control; jurisdiction and sovereignty; operating capacity; lifecycle cost and contracts; dependency; interoperability; portability and exit.
2. Record local evidence, assumptions, option-specific implications, trade-offs, evidence owner and validation status for every material criterion.
3. Detect duplicated criteria, unsupported scoring, automatic-outcome claims and contradictions between inputs.
4. Classify status as sufficient, needs validation, decision-blocking, suitable for a reversible pilot, or monitor during operation.
5. Return conditional next steps and specialist routes. Make clear that the matrix supports accountable local judgment and does not choose a provider, country policy or universal model.

## Output

```yaml
decision_matrix:
  criterion:
  requirement:
  local_evidence:
  assumption_or_unknown:
  option_implication:
  trade_off:
  evidence_owner:
  status:
  next_step:
```

## Boundaries

Do not create a numeric winner, infer missing local evidence, select a provider, or expose internal material. Cloud, SaaS, open source, standards and sovereignty are not automatic solutions.