from dataclasses import dataclass


@dataclass
class ActivationProfile:
    smdpp_address: str
    matching_id: str
    confirmation_code: str | None = None

    @property
    def full_activation_code(self) -> str:
        return f"LPA:1${self.smdpp_address}${self.matching_id}"

    @staticmethod
    def from_activation_code(activation_code: str) -> "ActivationProfile":
        if not activation_code.startswith("LPA:1$"):
            raise ValueError("Invalid activation code")

        parts = activation_code.split("$")
        assert len(parts) == 3

        return ActivationProfile(parts[1], parts[2])
