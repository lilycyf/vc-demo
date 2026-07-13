# Regulatory Network Artifact Acquisition Blocker

- Artifact: `regulatory_network_artifact`
- Status: `blocked_unavailable_or_undefined_source`
- Cell line: `K562`

## Checked Sources

- configs/artifacts/acquisition_sources.json: no entry/resolver for regulatory_network_artifact
- HuggingFace dataset API genbio-ai/foundation-models-perturbation recursive tree: no regulatory/regulon/GRN artifact; network-related matches were STRING/GNN/gene-embedding artifacts, not a regulatory-network artifact
- HuggingFace model API genbio-ai/STRING_GNN recursive tree: no regulatory-network artifact and no usable regulatory checkpoint/layout
- configs/artifacts/k562_registry.json and run artifact audit: regulatory_network_artifact not registered as present with path/provenance

## Reason

The selected official_regulatory_network_prior blueprint requires regulatory_network_artifact, but no source-backed artifact contract, path, resolver, row/gene-order contract, or verified public primary source was available. Substituting STRING graph edges, random GRN edges, or a proxy MLP would violate strict artifact policy.

## Strict Policy Decision

Do not implement or train fallback. Keep node as requires_artifact_acquisition and report as a valid strict blocker/exclusion until a real regulatory artifact is added.
