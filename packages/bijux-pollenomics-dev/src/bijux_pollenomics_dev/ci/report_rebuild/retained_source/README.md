# Retaining scientific execution source

First-party packages belong in `packages/` and their Git history. A scientific
capture retains its original scientific inputs, outputs, receipts and logical
input identities. It must not embed another package tree or hide that tree in
content-addressed payloads.

`configs/ci/source-retention/index.json` identifies the reviewed source transport
descriptors. Each descriptor binds the unchanged capture, original logical source
members and exact reachable canonical Git objects. Readers verify the Git object
type, path, reachability, byte count and original SHA-256. They read source bytes
in memory; they neither materialize nor import historical packages. Captures keep
their original native execution identities. A source-history correspondence does
not mean the corrected commit was executed.

The retained VCS version resource is reconstructed with a bounded serializer from
its declared scalar metadata and checked against its original byte identity.
This establishes content correspondence, without reconstructing the original
version calculation or claiming an original generator execution.

Verification requires a physical Git clone containing the referenced ancestors.
Missing source objects, shallow history and source archives without Git metadata
are explicit verification failures. Readers never fetch missing source, substitute
the current implementation or depend on unreachable recovery objects.

The package-layout checks reject new tracked `data/**/packages/**` snapshots and
content-addressed copies of canonical package modules. Its
single historical generated-resource exception predates the source-capture work;
it does not authorize new copied source trees. Original execution controllers
with no canonical Git source remain distinct retained evidence, as do scientific
data and logs that share bytes with a source resource.

Execution controllers that later became maintained modules may use a byte-exact
Git correspondence as a separate transport role. Their original controller paths,
input roles and execution epochs stay unchanged; a later canonical commit is a
source-byte authority, without an original execution claim.

The finite-covariance packet retains its original native execution at
`92a0adc1f00245c1a51b4e096e1eaac4c23325e5`. Its detached control-source members
resolve through the finite packet descriptor, including the exact execution
controller recorded under the historical `65fa003583dafcee24a5305c2b5a95e78184201b`
identity. That controller is a reachable Git witness at its maintained ownership
path, with no current executable copy. Its transport does not claim a new run.
All 67 tracked scientific inputs still require their captured byte identities.
The separate 539-byte VCS metadata correspondence authenticates declared scalar
content and makes neither an original-generator nor version-derivation claim.
