# Publication Geography Registry

This registry defines the governed report scopes used by the checked-in
publication tree. Country and regional outputs are derived views, not separate
publication families with their own ad hoc rules.

## Scope Inventory

| Scope | Kind | Parent | Directory | Published countries |
| --- | --- | --- | --- | ---: |
| World | `world` | `-` | `world` | `4` |
| Europe-plus | `region` | `world` | `regions/europe-plus` | `4` |
| Nordic | `region` | `europe_plus` | `regions/nordic` | `4` |
| Sweden | `country` | `nordic` | `countries/sweden` | `1` |
| Norway | `country` | `nordic` | `countries/norway` | `1` |
| Finland | `country` | `nordic` | `countries/finland` | `1` |
| Denmark | `country` | `nordic` | `countries/denmark` | `1` |

## Europe-plus Definition

Europe-plus means EU countries plus Norway and Switzerland. The current report
tree only publishes subsets that have present data in the repository, but the
definition itself is stable and broader than the current Nordic release slice.
