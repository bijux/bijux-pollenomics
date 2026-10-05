"""Strict original source and capture identities for the Nordic account."""

FAMILY = "docs/report/pollen-reconstruction/nordic-static-basin-scenarios"
DESCRIPTOR = FAMILY + "/inputs/retained-source-identities.json"
ORIGINAL_CAPTURE_PINS = {
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/assumptions/protocol.json": "c64342e2de92dd755af2b8136fdc5c95ea15da1d28790d3e12fc4ec891cea19c",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/diagnostics/summary.json": "7a6c95506ae45e37d2c3fc55b01b8be1b3551f91442bdd47686d3ae8c523add8",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/report.json": "50d2e11aa053f22afe8aeb2b0867c2ee3c00340ad002a6ece71c36aafdbbedfe",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/actual-first-party-import-closure.json": "42c519627404030a6a2706fbb034f9dfea3694778046f745a7a24baefc34c322",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/independent-physical-review.json": "ce27a738d2673396daf9555537671f6c06560ffe3501413c0f27d6e76938ec78",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/independent-physical-terminal.json": "419854788e096ef9dfa7a0e9c650df5cea762164331e1a0034aa18897464f7c8",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/independent-scalar-review.json": "d419615c986bccb09bb67e7af68508885502b2a56fe1030a6ca7b6f13f92e486",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/independent-scalar-terminal.json": "fc844afa08fe802f8800e6dd2ba2b4357896e36f67d1a1f4a412a003d3db384e",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/native-terminal.json": "b00ad8785bacb49d6e48e3060acd9229e31e2ea26e356b6057bc82b6f924577c",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/physical-response-tuples.json": "675e7ae2107829fd575255249f2643bde31951945b15690e46631455137be8e3",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/primary-policy-capture.json": "5b993764ce054b8ec428440b6c26634464bc9f6eee0686f1120815d41bac752e",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/primary-policy-native-terminal.json": "bb27d6224c2616d380dc1e9ba3a6f439f9e9e53be1fe57d9ae238ab20a1557bd",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/source-census-terminal.json": "4cf58a39d738f04c40e806b5f2ed716d7cf7327fe0003a2bceebbf4fe071af6f",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/source-census.json": "659a2fb5039b778ceb1879036f1a87238f7b021c3b2db5174fb66e582c262156",
}
PUBLICATION_CAPTURE_PINS = {
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/acquisition-terminal.json": "e5c3ef1e2fd56050bf2e67fd4676c42cdeb4b24745e677aa5715ce16a63f18e8",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/acquisition.json": "a9f38c757f147d55d8781e5b201ff7b3b0e6e5ff2e374fe6088e431611b7279b",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/dataset-20034.json": "37f16906353c1e2574ca99b1ce02cab5cde1a7e63acf3fe684810abead15f5ed",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/dataset-4445.json": "d6f43348d5c3a8e367ef15a154a61b9fd8e5d1e9ea7c994aab9c5da82ad89693",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/dataset-4446.json": "e259b6247bdc43645ea75c7e6911d62431f3ae89bb7f4c90472ddec9f2c4e189",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/dataset-52082.json": "3791c17a7b7f17c393fd0ec8d99970186aa4cb4219ca09d1ce0cb67a9f19a69b",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/qualification-terminal.json": "49043fd1e075d7c823a0c3c404324ad75ac9cd3a8ff53222439b39a9a9e055a7",
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/qualification.json": "7842db918ef4f02fc846f1edb6ba21d0c0269a66b88e9c95a9f67aff6a7914ea",
}
CAPTURE_PINS = {**ORIGINAL_CAPTURE_PINS, **PUBLICATION_CAPTURE_PINS}
DESCRIPTOR_SHA256 = "f903051acee72613bad110c2539f37c082d52a340966ddd79bbc03253e5453cc"
PUBLICATION_AUTHORITY = {
    "acquisition": {
        "candidate": "b20246a1d3307a5930355a96ca76734783417633",
        "plan_sha256": "b26977e999874fa576575fd1ef8eeff4a31471d0283aec2f4a65e116844f8fd8",
        "terminal_sha256": "e5c3ef1e2fd56050bf2e67fd4676c42cdeb4b24745e677aa5715ce16a63f18e8",
        "output_sha256": "a9f38c757f147d55d8781e5b201ff7b3b0e6e5ff2e374fe6088e431611b7279b",
    },
    "qualification": {
        "candidate": "b20246a1d3307a5930355a96ca76734783417633",
        "plan_sha256": "fa7732715e5c4f45344f6bde2abd2ab6047530c8c52adc58ce8f0869a6334f6a",
        "terminal_sha256": "49043fd1e075d7c823a0c3c404324ad75ac9cd3a8ff53222439b39a9a9e055a7",
        "output_sha256": "7842db918ef4f02fc846f1edb6ba21d0c0269a66b88e9c95a9f67aff6a7914ea",
    },
}
