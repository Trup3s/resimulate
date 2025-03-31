from dataclasses import dataclass


@dataclass
class Profile:
    smdpp_address: str
    matching_id: str
    confirmation_code: str | None = None

    def full_activation_code(self) -> str:
        return f"LPA:1${self.smdpp_address}${self.matching_id}"

    @staticmethod
    def from_activation_code(activation_code: str) -> "Profile":
        if not activation_code.startswith("LPA:1$"):
            raise ValueError("Invalid activation code")

        parts = activation_code.split("$")
        assert len(parts) == 3

        return Profile(parts[1], parts[2])
