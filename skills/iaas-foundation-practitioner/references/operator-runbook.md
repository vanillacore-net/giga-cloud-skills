# Chapter 3 operator runbook

This runbook turns the Chapter 3 practitioner skill into an executable workflow for an approved OpenStack project. It creates and validates tenant IaaS resources. It does not install or operate an OpenStack control plane.

## Operator-kit boundary

The checked-in kit is under `assets/operator-kit/`. Never write environment values, credentials, state, plans or live evidence into the installed skill directory. Create a protected working copy first. Practical execution requires Bash and POSIX filesystem semantics. On Windows, use WSL or an equivalent POSIX environment; otherwise use the skill for explanation and review only.

```bash
set -euo pipefail
SKILL_DIR=/absolute/path/to/installed/iaas-foundation-practitioner
WORK_ROOT=/absolute/path/to/protected/work
WORK_DIR="$WORK_ROOT/giga-chapter-3-operator"
test -f "$SKILL_DIR/SKILL.md"
test ! -e "$WORK_DIR"
umask 077
mkdir -p "$WORK_ROOT"
cp -R "$SKILL_DIR/assets/operator-kit" "$WORK_DIR"
export GIGA_OPERATOR_KIT="$WORK_DIR/lab"
cd "$GIGA_OPERATOR_KIT"
./scripts/offline-validate.sh
```

Resolve `SKILL_DIR` from the host's installed-skill path. The operator supplies `WORK_ROOT`. Do not guess either path.

## Operations

| Operation | Goal | Default mutation level |
|---|---|---|
| `assess` | Check tools, source pin, example integrity and required local inputs | None |
| `prepare` | Create the ignored local contract and prepare one reviewed interface path | Local files only |
| `provision` | Create the bounded server, port, security policy, floating IP and volume request | Live OpenStack change |
| `validate` | Join Nova, Neutron and Cinder state through stable IDs | Read-only |
| `maintain` | Re-read quota, placement, resource state and retained-data decisions | Read-only unless a separate change is approved |
| `cleanup` | Delete through dependency order or retain the volume deliberately, then prove the result | Live OpenStack change |

## Assess

1. Read `SOURCE.md`, `lab/README.md` and `lab/VERSIONS.yaml`.
2. Run `lab/scripts/offline-validate.sh` in the working copy.
3. Check for `python3`, the chosen OpenStack client or Horizon access, and `tofu` when OpenTofu is selected.
4. Record missing tools and inputs. Do not convert missing values into defaults.

Pass only when the source pin is present, offline validation passes, and the intended interface is explicit.

## Prepare

```bash
set -euo pipefail
cd "$GIGA_OPERATOR_KIT"
test ! -e environment-contract.yaml
cp environment-contract.example.yaml environment-contract.yaml
chmod 600 environment-contract.yaml
```

The operator must replace every example value and set `example_only: false`. Then run:

```bash
python3 scripts/preflight.py environment-contract.yaml
```

Choose exactly one creation path:

- Horizon: walkthroughs 02 and 03
- OpenStackClient: walkthrough 04
- OpenTofu: walkthrough 05

For OpenTofu, format, initialize without a backend, validate and save a reviewed plan. State and plans stay in the protected working copy.

## Live-change gate

Before `provision` or `cleanup`, require all of the following:

- an approved disposable project and protected `clouds.yaml` profile;
- a local contract that passes preflight without `--allow-example`;
- separately discovered Nova and Cinder placement inputs;
- supplied project, region, image, flavor, network, CIDR and quota facts;
- one selected interface path;
- a reviewed request or OpenTofu plan;
- an explicit operation-specific approval;
- a cleanup or retention decision made before creation.

If any condition is absent, stop at `prepared` or `unverified`.

## Provision

Execute only the selected walkthrough. Do not run Horizon, OpenStackClient and OpenTofu creation paths against the same names in one project. Capture the cloud profile and stable IDs in the ignored `evidence/resource-ids.json` file immediately after creation.

A successful create command is not acceptance. Continue to validation.

## Validate

From the working kit, run `scripts/verify-resource-chain.sh` with the supplied cloud profile and captured server, port, security-group, floating-IP and volume IDs. The verifier checks exact relationships across Nova, Neutron and Cinder.

Report guest login, DNS, TLS, application health, backup and recovery as `not-tested` unless separate evidence exists. They are outside this IaaS result.

## Maintain

Use read-only service queries to check:

- project scope and catalogue;
- quota and current use, separately from physical capacity;
- server, port, floating-IP and volume state;
- volume attachment and retained-data ownership;
- drift between the approved contract and live identifiers.

Any resize, network-policy change, attachment change or replacement is a new live operation. Prepare its exact request, validation and recovery path before asking for approval.

## Cleanup

Preserve identifiers before deletion. Follow walkthrough 07 and stop on failed detach, terminal error or timeout. Deletion is accepted only when `scripts/verify-absence.sh` proves absence by captured ID. A retained volume must be `available` with no attachments.

## Operator result

Return this record with the Chapter 3 handoff:

```yaml
operator_execution:
  kit_source:
  operation:
  working_directory:
  execution_level: explained | prepared | offline-validated | live-executed
  change_approval:
  checks: []
  changed_resource_ids: []
  evidence: []
  rollback_or_cleanup:
  status: passed | failed | blocked | unverified
```

Never include credentials, token values, private keys, `clouds.yaml` contents, OpenTofu state or saved plan bodies in the response.
