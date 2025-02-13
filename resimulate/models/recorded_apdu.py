from osmocom.utils import b2h, i2h
from pySim.apdu import Apdu, ApduCommand


class RecordedApdu:
    def __init__(self, apdu: Apdu, command: ApduCommand) -> None:
        self.apdu = apdu
        self.name = command._name
        self.path = command.path_str
        self.command_dict = command.to_dict()

    def __str__(self) -> str:
        return f"{self.name} {self.path} -> {self.__apdu_str}"

    @property
    def __apdu_str(self) -> str:
        return f"{type(self).__name__}(cla={b2h([self.apdu.cla])} ins={i2h([self.apdu.ins])} p1={i2h([self.apdu.p1])} p2={i2h([self.apdu.p2])} lc={i2h([self.apdu.lc])} data={b2h(self.apdu.cmd_data)} p3/le={i2h([self.apdu.p3])})"

    def __rich__(self):
        return f"[bold green]{self.name} [bold blue]{self.path} -> {self.__apdu_str}[/]"
