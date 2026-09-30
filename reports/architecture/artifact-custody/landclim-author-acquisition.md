# Why we retired the released LandClim author checkout

We retained the exact released `rmfyfe/landclimII` source before removing its
inactive `artifacts/v2/` acquisition directory. The private source store owns
the 51-file author tree used by our two-grid calculation and WHH05 source
test. It also now owns the original GitHub tarball, commit response and HTTP
receipt. The [custody record](landclim-author-acquisition.json) binds the
original checkout, archive and copied acquisition files by SHA-256.

We compared every original author file with the private `author` tree and
checked its path, byte count and SHA-256 against the acquisition receipt.
All 51 paths and 597,506 file bytes matched, with no extra private author
members. The original 115,204-byte tarball had SHA-256
`cd6cc688e6c44dd61d0ed038f53d118f4aade0696c37dc6174d613a38097bb38`.
The tarball, 6,107-byte commit response and 9,616-byte receipt were copied
byte for byte to `landclim/author-reference/acquisition/` in the private
source store. The retired artifact prefix contained 54 regular files and
728,433 bytes in total. It had no symlinks, hardlinks or open handles.

The [WHH05 integration test](../../../packages/bijux-pollenomics-dev/tests/essd_reproduction/test_one_site.py)
now reads the private capsule only when its source variable is supplied. No
tracked product reader points to the retired artifact path. Our
[source-to-estimate account](../../science/publication-correspondence/author-example-site-replay.md)
records the bounded numerical result and its remaining source limits.
Removing the duplicate checkout does not identify the historical Nordic
publication inputs or clear redistribution rights for the retained source.
