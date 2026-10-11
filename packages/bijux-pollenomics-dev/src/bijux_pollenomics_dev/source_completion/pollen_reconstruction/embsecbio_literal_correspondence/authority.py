"""Bind the original correspondence study and its private retained source store."""

from pathlib import Path

SOURCE_ID = "embsecbio/literal-count-percentage-correspondence"
DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/embsecbio-literal-correspondence.json"
)
DESCRIPTOR_SHA256 = "accbf3495f64361c76009b5f901a4fa205bf1d36c0a3dcd99d8945e49035d18e"
CAPTURE = Path(
    "data/method-certification/embsecbio-literal-correspondence/source-capture.json"
)
CAPTURE_SHA256 = "ead43ed850b4a0947f1ab0eb18aa50d678c600f4922e2f2cb60db81275e1d4f6"
SOURCE_SHA256 = {
    "alternate-source-discovery.json": "1a2a879b86202e51fabfd76f78a11b222b110e6735b80405882c579773b2f7ae",
    "bridge-attempt-population.json": "ed2070cb67db77a6f3aae62b1e9adacce231e3e0b7d229bb9bc9bbfd7d41972a",
    "candidate-source-rows.json": "d5de400e484cbee2236ef02acc8f8671bfc53e1a7bbf792bd5c50ababff1fad5",
    "correspondence-diagnostics.json": "ab004d58e303f52d75ee74ed36565e7614361f30c5eacd5438f2d8424740bde6",
    "diagnostic-plan.json": "563c3ebce2d4bed94304d0a7d3b811d6a0d66b31b303c39c3c462b50c61c6f51",
    "full-vector-source-account.json": "46fac059d014061df3e9472f4ebe18b3a540225abf9dc25ba45386e6c5908422",
    "independent-source-review.json": "321002cf435f3243e6ad16b427cf1049b99f0a2b130d776b777ba235fabd49b6",
    "native-terminal.json": "e0c489ded63db5bd7f368007612f34d3290733941a6e01340f5b4ba1010fda5d",
    "original-curated-acquisition-terminal.json": "a7945bfde3ffaa609d0088a122ed0ad2794a65437111c3795ebce3ae124cdfac",
    "original-diagnostic-producer.py": "8da8413604b391388430bfadd02194136552c6c40c22dc96e73063fed242a005",
    "original-input-identities.json": "45ef2d7628b9f27cc181b4a650e281612c6ad4090fe4b52ce4b912a9edd4980c",
    "original-native-join-terminal.json": "f6c2a014535ea26619f3e917c199762f1383a8bc12cb888d85ca8b446e990fd0",
    "raw-relations-summary.json": "a6d0a89fdd61d8765d64ee27635f792c81150ffb4ad5f9a8a76acf76d22f1655",
    "refused-source-population.json": "3605758a584f569e12fa1b5c68092a378310296fe9e6fee5ed1279be4966892c",
    "source-account.json": "3ddf25174c8df7b32beea58f88fb3712abaa6704c8f851b549e17e8db5894cdd",
    "source-guards.json": "4c4119a736fd5d26c892d72430683f6977066898c3404e02419c2c905f4558bd",
    "supplement-access-account.json": "4c668e49447551c913d583bd29ca0a3fa80cf00cce7b0ac70d4d03833b267838",
    "supplement-access-terminal.json": "626fe7dfd14eeee08e7befbfea4e08e561070e05159fa8a4902ed529c1e207e2",
}
