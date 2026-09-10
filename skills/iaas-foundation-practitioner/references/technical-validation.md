# Chapter 3 syntax and evidence validation

Use the narrowest check that can test the claim. Report the command, tool version when material, exit status, and captured evidence reference. Do not report a stronger status than the performed check supports.

## Validation ladder

1. **Text and parser:** JSON, YAML, shell, or HCL parses.
2. **Tool syntax:** the installed client accepts the options; OpenTofu formats and validates against the selected provider schema.
3. **Non-mutating environment check:** authentication, catalogue, project scope, service discovery, quota, and resource inputs are read back.
4. **Planned change:** a reviewed API request, Horizon field set, or OpenTofu plan identifies the intended resources and values.
5. **Live resource state:** each owning service returns the expected state by stable ID within a bounded wait.
6. **Cross-service relationship:** structured results prove the exact server, port, security group, floating IP, and volume links.
7. **Cleanup or retention:** exact IDs are absent, or retained data has the expected safe state.

## Syntax rules

- Shell: use `sh -n` or `bash -n` according to the declared interpreter. This does not execute commands.
- JSON and YAML: parse with a real parser. This does not check cloud semantics.
- OpenStackClient: check the installed version and subcommand help or current official documentation before emitting executable syntax.
- OpenTofu: run `tofu fmt -check`, `tofu init -backend=false`, and `tofu validate`. Review a saved plan before an approved apply. Keep state, plans, and credentials out of Git.
- Horizon: name navigation, field, exact supplied value, confirmation, expected state, and read-back. A screenshot must show the result it claims.

## Safe read-back patterns

The following patterns are appropriate only after the named variables have been supplied and shell-quoted safely:

```bash
openstack --os-cloud "$CLOUD_PROFILE" server show "$SERVER_ID" -f json
openstack --os-cloud "$CLOUD_PROFILE" port list --server "$SERVER_ID" -f json
openstack --os-cloud "$CLOUD_PROFILE" floating ip show "$FLOATING_IP_ID" -f json
openstack --os-cloud "$CLOUD_PROFILE" volume show "$VOLUME_ID" -f json
```

Confirm these commands against the installed client before classifying them as executable. Never print credential material or the contents of `clouds.yaml`.

## Evidence claims

- Authentication success proves only that the client obtained a scoped response.
- A server `ACTIVE` state proves only the Nova server state.
- An active port or floating IP proves only its Neutron state and relationship.
- A volume `in-use` state needs attachment read-back to prove which server uses it.
- A successful OpenTofu apply proves requested provider operations completed, not that the service is usable.
- IaaS acceptance does not prove guest, application, DNS, TLS, backup, recovery, or user-journey acceptance.

## Failure handling

Every asynchronous wait needs a time bound, accepted states, terminal failure states, and a non-zero or visible failure result. Zero or multiple discoveries must stop a path that requires exactly one result.
