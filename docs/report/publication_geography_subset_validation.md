# Publication Geography Subset Validation

This review proves that narrower publication scopes remain explainable subsets
of broader scopes instead of silently drifting into separate artifact families.

## Scope Checks

| Scope | Parent | Country subset | Animal subset | Human subset |
| --- | --- | --- | --- | --- |
| Europe-plus | World | `true` | `true` | `true` |
| Nordic | Europe-plus | `true` | `true` | `true` |
| Sweden | Nordic | `true` | `false` | `true` |
| Norway | Nordic | `true` | `true` | `true` |
| Finland | Nordic | `true` | `true` | `true` |
| Denmark | Nordic | `true` | `false` | `true` |
