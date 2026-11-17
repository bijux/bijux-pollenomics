---
title: Report Publication Ownership
audience: maintainer
type: reference
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-11-17
---

# Report Publication Ownership

`reporting.bundles.staging.publish_into_staging_dir` gives each eager report
callback its own private candidate directory. The callback keeps its existing
`Path` argument and return value. It must finish and close its writes before
returning. Country, Atlas and partition publishers retain their logical final
output paths; the private construction path is not the published report path.

The original candidate root is created exclusively by `OwnedTreeWriter` and
keeps that physical identity through publication. The shared core callback
completion seal inventories every ordinary file and directory after the callback. It
refuses aliases, multiply linked files and nonregular members, and preserves
ordinary empty directories and Unicode names. It binds the complete namespace,
file sizes and physical identities through final attachment. This is explicit
support for trusted Path callbacks; it does not broaden the normal bounded
writer's authored-file contract or admit external scientific inputs.

The existing `publish_owned_replacement` owner performs descriptor-bound,
no-replace attachment and predecessor recovery. A callback cannot borrow another
operation's candidate or silently adopt a destination that appeared during its
work. Newly created public parents retain ordinary creation permissions under
the process umask; recovery directories retain private permissions. Fixed `.report.staging` and `.report.recovery` siblings are not cleanup
authority. Foreign entries are preserved. Concurrent operations may refuse;
path names do not constitute writer ownership. The composite candidate checks
the already-held original destination parent inside the replacement owner's
attachment methods. A new foreign parent at the same pathname cannot become
publication authority through a fresh lookup.

A semantic `validate` callback, when supplied, runs on the sealed candidate
before attachment and again on final readback. Partition publication uses this
boundary for its existing path contract, so an invalid partition cannot replace
a prior complete tree. Successful partition results retain that validated
inventory rather than starting a fresh inventory after publication.

Collection callbacks use the same core owner through their own wrapper; see
[collection publication](collection-publication.md) for legacy recovery and
replacement metadata compatibility. Report replacement and completion injection
seams continue to delegate at the report wrapper boundary.

## Recovery And Failure

Each operation retains a private recovery directory outside its final report.
An identified destination repository owns recovery under its `artifacts/`
directory; standalone destinations use same-volume external sibling storage.
Nested report callbacks use their active outer operation's held external
recovery anchor, so predecessor files cannot leak into the outer report.
Copied execution contexts cannot extend that callback storage lease. Live
callback-root capabilities are also discoverable by ordinary worker threads;
the registry holds only operation metadata and anchors, never report bodies. The
live registry is process-local: nested publisher calls belong to that process;
separate processes publish independent roots.
Children must finish before the outer callback returns. An incomplete child
publication refuses the outer commit before its namespace is sealed or attached.
A closed callback stays unavailable during validation and attachment, so late
worker entry cannot silently fall back to storage inside its candidate. The
nearest registered physical ancestor owns that decision, including closed or
moved child roots; an active outer scope cannot lend its lease to that child.
Only when no physical capability is observed does lookup use the most specific
original pathname or inherited context to refuse a displaced attachment.

Callback failure and cancellation preserve the original exception and prior
output. Attachment or final validation failures restore a verified predecessor
when the final path is available. If a competing foreign destination occupies
that path, it is preserved and the complete predecessor remains in recovery.
Recovery and refused candidates are retained for review; publication does not
delete them. Failure notes identify their expected location and directory
identity, whose current attachment must be checked before recovery work.

The owner uses the existing Darwin/Linux descriptor and exclusive-rename
primitives. Unsupported filesystems or platforms refuse; there is no racy
check-then-replace fallback. Physical checks are boundary seals, not an OS inode
compare-and-swap guarantee against arbitrary intervening filesystem mutation.
A later authorized publication may replace an earlier committed result.

## Resource Contract

Legacy trusted Path callback generation has no accepted whole-report byte or
file ceiling. Publication does not claim to bound that preceding work. The
completed metadata census derives finite bounds and exact membership for
subsequent attachment and growth checks. It does not copy candidate bodies.
Predecessor validation retains the existing replacement owner's bounded streamed
checks; a representative control observes both prior checks and no candidate
body read by the completion seal.

Atlas view, initial-load, interaction and asset budgets remain separate and
unchanged. They are not whole-report ceilings. Whole-report generation cost,
retained recovery storage and performance still require a separately scoped
profile; this ownership boundary does not certify a large report rebuild or
its scientific inputs.
