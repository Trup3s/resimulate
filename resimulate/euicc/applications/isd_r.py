import logging

from pySim.euicc import (
    EuiccConfiguredAddresses,
    EuiccInfo2,
    EuiccInfo1,
    GetEuiccChallenge,
    GetEuiccData,
    TagList,
)

from resimulate.euicc.applications import Application
from resimulate.euicc.models.profile import Profile


class ISDR(Application):
    aid = "A0000005591010FFFFFFFF8900000100"
    name = "ISDR"
    alternative_aids = [
        "A0000005591010FFFFFFFF8900050500",  # 5Ber.esim
    ]

    def get_euicc_challenge(self) -> str:
        euicc_challenge = self.store_data_tlv("get_euicc_challenge", GetEuiccChallenge)
        return euicc_challenge.to_dict().get("get_euicc_challenge")[0][
            "euicc_challenge"
        ]

    def get_euicc_info_1(self) -> list[dict]:
        command = self.store_data_tlv("get_euicc_info_1", EuiccInfo1)
        euicc_info = command.to_dict().get("euicc_info1")
        return self._merge_dicts(euicc_info)

    def get_euicc_info_2(self) -> list[dict]:
        command = self.store_data_tlv("get_euicc_info_2", EuiccInfo2)
        euicc_info = command.to_dict().get("euicc_info2")
        return self._merge_dicts(euicc_info)

    def get_configured_addresses(self) -> str:
        command = self.store_data_tlv(
            "get_configured_addresses", EuiccConfiguredAddresses
        )
        addresses = command.to_dict().get("euicc_configured_addresses")
        return self._merge_dicts(addresses)

    def get_eid(self) -> str:
        command = GetEuiccData(children=[TagList(decoded=[0x5A])])
        eid_data = self.store_data_tlv("get_eid", command, GetEuiccData)
        return eid_data.to_dict().get("get_euicc_data")[0]["eid_value"]

    def initiate_authentication(self, profile: Profile):
        smdpp_address = profile.smdpp_address
        if not smdpp_address:
            smdpp_address = self.get_configured_addresses().get("smdpp_address")

        logging.info(f"Initiating authentication with {smdpp_address}")
        challenge = self.get_euicc_challenge()
        return challenge

    def download_profile(self, profile: Profile):
        smdpp_address = profile.smdpp_address
        if not smdpp_address:
            smdpp_address = self.get_configured_addresses().get("smdpp_address")

        logging.info(f"Downloading profile from {smdpp_address}")
        # challenge = self.get_euicc_challenge()
