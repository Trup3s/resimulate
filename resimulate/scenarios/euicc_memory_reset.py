from resimulate.euicc.card import Card
from resimulate.euicc.models.activation_profile import ActivationProfile
from resimulate.euicc.models.reset_option import ResetOption
from resimulate.scenarios.models.scenario import Scenario


class EuiccMemoryResetScenario(Scenario):
    def run(self, card: Card):
        profile = ActivationProfile.from_activation_code(
            "LPA:1$rsp.truphone.com$QR-G-5C-1LS-1W1Z9P7"
        )

        card.isd_r.set_default_dp_address("test")
        address = card.isd_r.get_configured_data().default_dp_address
        assert address == "test"

        card.isd_r.reset_euicc_memory(ResetOption.RESET_DEFAULT_SMDP_ADDRESS)

        address = card.isd_r.get_configured_data().default_dp_address
        assert address == ""

        card.isd_r.download_profile(profile)
        profiles = card.isd_r.get_profiles()
        assert len(profiles) > 0

        card.isd_r.reset_euicc_memory(ResetOption.DELETE_OPERATIONAL_PROFILES)

        profiles = card.isd_r.get_profiles()
        assert len(profiles) == 0
