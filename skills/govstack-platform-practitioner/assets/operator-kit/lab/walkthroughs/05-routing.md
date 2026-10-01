# 05: Connect both Spokes

Each workload Spoke already has its own private Contour/Envoy ingress. We now place a distinguishable test service behind each one and connect the shared route to the correct ingress address.

## Prepare the local service and certificate

The session provides two distinct domains, private Envoy addresses, an explicit certificate issuer and a digest-pinned HTTP-echo-compatible image. The helper's image arguments are `-listen=:8080` and `-text=<cluster-name>`; an arbitrary image serving HTTP is not sufficient. The verified example image in the lab README supports those flags.

```bash
"$PYTHON" "$LAB/scripts/platform.py" route --case "$CASE"
```

The real upstream Envoy Helm chart is rendered before files are saved. The output contains edge values/rendered manifests and one probe manifest for each Spoke. Each probe defines Deployment, Service, Certificate and HTTPProxy. Its response is the target cluster name. Certificate issuance and HTTPS termination are local to the selected Spoke.

A live site must provide the referenced Issuer or ClusterIssuer in each cluster and the necessary CA or ACME configuration. The helper does not create issuer credentials. A namespaced Issuer must be in `chapter5-probe`; a ClusterIssuer belongs to the platform. Never put its private key in Git.

## Deliver through the right owner

The generated Namespace is a platform preparation artifact. When Workload Argo CD's tenant foundation already owns it, omit that Namespace document from the team application repository. Deploy only the namespaced Deployment, Service, Certificate and HTTPProxy through the team's permitted AppProject. Do not ask namespaced Workload Argo CD to create a namespace or ClusterIssuer.

After private ingress works, publish the reviewed edge route values through the LoadBalancer foundation's deployment repository. Point each backend at the selected private Envoy service address, not a Pod address or Kubernetes API endpoint. Review the gateway forwarding configuration separately. The request path is:

`client -> public gateway -> LoadBalancer routing -> private Spoke Envoy -> Service -> Pods`.

## Observe the real response

For an approved live case, first test each Spoke's private ingress from a permitted administration route, preserving the intended hostname and certificate trust. Then test the public path:

```bash
"$PYTHON" "$LAB/scripts/platform.py" probe --case "$LIVE_CASE" --target mediator
"$PYTHON" "$LAB/scripts/platform.py" probe --case "$LIVE_CASE" --target examples
```

The probe uses `curl --resolve` to test the given edge address with the correct TLS name, verifies trust and requires the exact response marker. It deliberately does not prove DNS publication or every backend identity. Check ordinary DNS separately and inspect the delivered route, private ingress, Service endpoints and Pods when diagnosing a failure. Never replace certificate validation with `--insecure`.

In example mode both live probes refuse. The offline suite instead exercises an actual local HTTPS server, a trusted local test certificate and a wrong response marker. It proves that client behavior, not a deployed platform.
