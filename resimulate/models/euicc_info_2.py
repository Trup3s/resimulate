from dataclasses import dataclass


@dataclass
class EuiccInfo2Data:
    profile_version: str
    svn: str
    euicc_firmware_version: str
    ext_card_resource: str
    uicc_capability: str
    ts102241_version: str
    global_platform_version: str
    rsp_capability: str
    euicc_ci_pki_list_for_verification: list[dict[str, str]]
    euicc_ci_pki_list_for_signing: list[dict[str, str]]
    pp_version: str
    sas_accreditation_number: str

    @staticmethod
    def from_list(obj: list[dict[str, str]]) -> "EuiccInfo2Data":
        return EuiccInfo2Data(
            profile_version=obj[0]["profile_version"],
            svn=obj[1]["svn"],
            euicc_firmware_version=obj[2]["euicc_firmware_ver"],
            ext_card_resource=obj[3]["ext_card_resource"],
            uicc_capability=obj[4]["uicc_capability"],
            ts102241_version=obj[5]["ts102241_version"],
            global_platform_version=obj[6]["global_platform_version"],
            rsp_capability=obj[7]["rsp_capability"],
            euicc_ci_pki_list_for_verification=obj[8][
                "euicc_ci_pki_list_for_verification"
            ],
            euicc_ci_pki_list_for_signing=obj[9]["euicc_ci_pki_list_for_signing"],
            pp_version=obj[11]["pp_version"],
            sas_accreditation_number=obj[12]["ss_acreditation_number"],
        )

    def __repr_rich__(self) -> str:
        return f"EuiccInfo2(profile_version={self.profile_version!r}, svn={self.svn!r}, euicc_firmware_version={self.euicc_firmware_version!r}, ext_card_resource={self.ext_card_resource!r}, uicc_capability={self.uicc_capability!r}, ts102241_version={self.ts102241_version!r}, global_platform_version={self.global_platform_version!r}, rsp_capability={self.rsp_capability!r}, euicc_ci_pki_list_for_verification={self.euicc_ci_pki_list_for_verification!r}, euicc_ci_pki_list_for_signing={self.euicc_ci_pki_list_for_signing!r}, pp_version={self.pp_version!r}, sas_accreditation_number={self.sas_accreditation_number!r})"
