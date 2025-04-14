import asn1tools

asn = asn1tools.compile_files(
    [
        "resimulate/asn/pkix1_explicit_88.asn",
        "resimulate/asn/pkix1_implicit_88.asn",
        "resimulate/asn/pe_definitions_v3_4.asn",
        "resimulate/asn/rsp_definitions_v2_6.asn",
    ],
    codec="ber",
    cache_dir=".asn_cache",
)
