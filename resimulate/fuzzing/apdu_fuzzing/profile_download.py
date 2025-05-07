from resimulate.euicc.card import Card
from resimulate.euicc.models.activation_profile import ActivationProfile
from resimulate.scenarios.models.scenario import Scenario


class ProfileDownloadScenario(Scenario):
    def run(self, card: Card):
        profile = ActivationProfile.from_activation_code(
            "LPA:1$rsp.truphone.com$QR-G-5C-1LS-1W1Z9P7"
        )
        notification = card.isd_r.download_profile(profile)
        iccid = notification.data.notification.iccid
        card.isd_r.process_notifications([notification])
        card.isd_r.enable_profile(iccid)
        card.isd_r.disable_profile(iccid)

        notifications = card.isd_r.retrieve_notification_list()
        card.isd_r.process_notifications(notifications)
