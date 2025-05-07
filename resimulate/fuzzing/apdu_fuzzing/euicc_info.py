from resimulate.euicc.card import Card
from resimulate.fuzzing.apdu_fuzzing.models.scenario import Scenario


class EuiccInfoScenario(Scenario):
    def run(self, card: Card):
        card.isd_r.get_euicc_info_2()
        card.isd_r.get_euicc_info_1()
