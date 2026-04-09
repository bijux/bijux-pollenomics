# Make Architecture

The `makes/` tree is organized as a layered make system with stable entrypoints and shared implementation modules.

## Target Shape

```
makes/
├── api/
├── bijux-py/
├── package/
├── packages/
├── env.mk
├── packages.mk
├── publish.mk
└── root.mk
```

## Neighbor Contract

Each repository also carries a sibling `configs/` tree that provides the shared tool configuration consumed by the `bijux-py/` modules:

```
configs/
├── coveragerc.ini
├── deptry.toml
├── mypy.ini
├── package-lock.json
├── package.json
├── pytest.ini
├── ruff.toml
└── schemathesis.toml
```

## Layer Roles

- `bijux-py/`: byte-identical shared implementation modules that must stay in sync across every Bijux Python repository.
- `api/`: repository-local API policy. Keep only local contract-freeze or drift commands here.
- root `*.mk`: repo-local package archetypes and repository-specific policy that are genuinely local to one repository.
- `packages/`: leaf package profiles. These declare package-specific policy and package-specific commands only.
- `env.mk`: repository-local environment policy and repository-specific command defaults.
- `packages.mk`: repository package inventory, aliases, and root-target routing metadata.
- `publish.mk`: repository-local publication policy layered on top of the shared publication workflow.
- `root.mk`: repository entrypoint that composes shared root orchestration with repository-specific commands.

## Design Rules

- Keep `bijux-py/` implementation-first and shared-first. If logic is generic, it belongs here.
- Keep `api/` local-only. Shared API contract and live-contract behavior belongs in `bijux-py`.
- Keep repo-local archetypes in clearly named root makefiles. If a package archetype is shared, include the `bijux-py` module directly from the package profile.
- Keep `packages/*.mk` focused on one package each. Shared defaults belong in archetypes, not repeated in every profile.
- Keep repository policy local. If a setting depends on repo identity, repo paths, or repo release policy, it belongs outside shared modules.
- Prefer durable names that describe intent and scope, not temporary rollout language.

## Verification

- `make check-shared-bijux-py`: verifies shared `bijux-py` modules are identical across sibling repositories.
- `make check-config-layout`: verifies the repository `configs/` tree exposes the full shared tool configuration surface.
- `make check-make-layout`: verifies the repository `makes/` tree contains the expected directories, wrapper entrypoints, and package profiles.

## Refactoring Heuristic

When a change touches more than one package profile or more than one repository, first ask whether it should become:

1. a shared `bijux-py` module,
2. a repo-local archetype in a clearly named `makes/*.mk` file, or
3. a single package-specific setting in `makes/packages/*.mk`.

Choose the highest layer that keeps the policy honest.
