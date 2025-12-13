# Rule Schema

Each rule in `doctrine/rules/` uses the following fields:

- `id`: stable identifier (string)
- `title`: human-readable label
- `pillar`: top-level grouping (e.g., Safety, Privacy, Governance)
- `category`: sub-area (e.g., Crisis, Fraud, Deepfakes)
- `severity`: `info`, `warn`, or `block`
- `priority`: integer ordering (lower runs first)
- `version`: semantic version string for lifecycle tracking
- `triggers`: list of keywords/patterns used by the simple matcher
- `conditions`: optional context flags to scope the rule
- `action`: `allow`, `warn`, or `block`
- `explain`: short rationale shown in decisions
- `remediation`: optional safer alternative or next step

Rules are sorted by `(priority, id)` to keep deterministic outcomes. Bundle versions are declared in each YAML to allow migrations and changelogs.
