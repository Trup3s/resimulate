from pySim.utils import sw_match


class EuiccException(Exception):
    """Base class for all exceptions raised by the eUICC."""

    pass


class ApduException(EuiccException):
    """Exceptions raised by the euicc via APDU commands."""

    SW_CODES = {
        "9000": "Normal ending of the command",
        "91??": "Normal ending of the command, with extra information from the proactive UICC containing a command for the terminal",
        "92??": "Normal ending of the command, with extra information concerning an ongoing data transfer session",
        "9300": "SIM Application Toolkit is busy. Command cannot be executed at present, further normal commands are allowed",
        "61??": "Command successfully executed; ‘??’ bytes of data are available and can be requested using GET RESPONSE.",
        "6200": "No information given, state of non-volatile memory unchanged",
        "6281": "Part of returned data may be corrupted",
        "6282": "End of file/record reached before reading Le bytes or unsuccessful search",
        "6283": "Selected file invalidated/disabled; needs to be activated before use",
        "6284": "Selected file in termination state",
        "62f1": "More data available",
        "62f2": "More data available and proactive command pending",
        "62f3": "Response data available",
        "63f1": "More data expected",
        "63f2": "More data expected and proactive command pending",
        "63c?": "Command successful but after using an internal update retry routine X times",
        "6400": "No information given, state of non-volatile memory unchanged",
        "6500": "No information given, state of non-volatile memory changed",
        "6581": "Memory problem",
        "6700": "Wrong length",
        "67??": "The interpretation of this status word is command dependent",
        "6b00": "Wrong parameter(s) P1-P2",
        "6d00": "Instruction code not supported or invalid",
        "6e00": "Class not supported",
        "6f00": "Technical problem, no precise diagnosis",
        "6f??": "The interpretation of this status word is command dependent",
        "6800": "No information given (The request function is not supported by the card)",
        "6881": "Logical channel not supported",
        "6882": "Secure messaging not supported",
        "6900": "No information given (Command not allowed)",
        "6981": "Command incompatible with file structure",
        "6982": "Security status not satisfied",
        "6983": "Authentication/PIN method blocked",
        "6984": "Referenced data invalidated",
        "6985": "Conditions of use not satisfied",
        "6986": "Command not allowed (no EF selected)",
        "6989": "Command not allowed - secure channel - security not satisfied",
        "6a80": "Incorrect parameters in the data field",
        "6a81": "Function not supported",
        "6a82": "File not found",
        "6a83": "Record not found",
        "6a84": "Not enough memory space",
        "6a86": "Incorrect parameters P1 to P2",
        "6a87": "Lc inconsistent with P1 to P2",
        "6a88": "Referenced data not found",
        "6a89": "File already exists",
        "6a8a": "DF name already exists",
        "6af0": "Wrong parameter value",
        "6a??": "RFU",
        "9850": "INCREASE cannot be performed, max value reached",
        "9862": "Authentication error, application specific",
        "9863": "Security session or association expired",
        "9864": "Minimum UICC suspension time is too long",
    }

    def __init__(self, sw: str):
        self.sw = sw
        self.message = "Unknown status word"

        for code, message in self.SW_CODES.items():
            if sw_match(sw, code):
                self.message = message
                break

        super().__init__(f"{self.sw} -> {self.message}")


class ProfileInstallationException(EuiccException):
    """Base class for all exceptions raised by the profile installation."""

    message: str = "An unknown profile installation error occurred"

    def __init__(self, bpp_command_id: int):
        self.bpp_command_id = bpp_command_id
        self.bpp_command = self.get_bpp_command(bpp_command_id)

        super().__init__(f"{self.bpp_command} -> {self.message}")

    @staticmethod
    def get_bpp_command(command_id: int) -> str:
        return {
            0: "initialiseSecureChannel",
            1: "configureISDP",
            2: "storeMetadata",
            3: "storeMetadata2",
            4: "replaceSessionKeys",
            5: "loadProfileElements",
        }.get(command_id, "UnknownCommand")

    @staticmethod
    def raise_from_result(error_result: dict):
        """Raises the appropriate exception subclass based on the error result."""
        error_map = {
            1: IncorrectInputValues,
            2: InvalidSignature,
            3: InvalidTransactionID,
            4: UnsupportedCRTValues,
            5: UnsupportedRemoteOpType,
            6: UnsupportedProfileClass,
            7: SCP03TStructureError,
            8: SCP03TSecurityError,
            9: IccidAlreadyExists,
            10: InsufficientMemory,
            11: InstallInterrupted,
            12: PEProcessingError,
            13: DataMismatch,
            14: InvalidNAAKey,
            15: PPRNotAllowed,
            127: UnknownInstallError,
        }

        error_reason = error_result.get("errorReason")
        bpp_command_id = error_result.get("bppCommandId")
        exception_class = error_map.get(error_reason, ProfileInstallationException)

        raise exception_class(bpp_command_id=bpp_command_id)


class IncorrectInputValues(ProfileInstallationException):
    message = "Incorrect input values"


class InvalidSignature(ProfileInstallationException):
    message = "Invalid signature"


class InvalidTransactionID(ProfileInstallationException):
    message = "Invalid transaction ID"


class UnsupportedCRTValues(ProfileInstallationException):
    message = "Unsupported CRT values"


class UnsupportedRemoteOpType(ProfileInstallationException):
    message = "Unsupported remote operation type"


class UnsupportedProfileClass(ProfileInstallationException):
    message = "Unsupported profile class"


class SCP03TStructureError(ProfileInstallationException):
    message = "SCP03T structure error"


class SCP03TSecurityError(ProfileInstallationException):
    message = "SCP03T security error"


class IccidAlreadyExists(ProfileInstallationException):
    message = "ICCID already exists on eUICC"


class InsufficientMemory(ProfileInstallationException):
    message = "Insufficient memory for profile"


class InstallInterrupted(ProfileInstallationException):
    message = "Install failed due to interruption"


class PEProcessingError(ProfileInstallationException):
    message = "PE processing error"


class DataMismatch(ProfileInstallationException):
    message = "Data mismatch"


class InvalidNAAKey(ProfileInstallationException):
    message = "Invalid NAA key"


class PPRNotAllowed(ProfileInstallationException):
    message = "PPR not allowed"


class UnknownInstallError(ProfileInstallationException):
    message = "Unknown installation error"


class NotificationException(EuiccException):
    """Base class for all exceptions raised by the notification handling."""

    message: str = "An unknown notification error occurred"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message

        super().__init__(self.message)

    def raise_from_result(result: int):
        """Raises the appropriate exception subclass based on the result."""
        error_map = {
            127: UndefinedNotificationError,
        }

        exception_class = error_map.get(result, NotificationException)

        raise exception_class()


class UndefinedNotificationError(NotificationException):
    message = "Undefined notification error occurred"


class ProfileInteractionException(EuiccException):
    """Base class for all exceptions raised by the profile handling."""

    message: str = "An unknown profile interaction error occurred"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message

        super().__init__(self.message)

    @staticmethod
    def raise_from_result(result: int):
        """Raises the appropriate exception subclass based on the result."""
        error_map = {
            1: IccidOrAidNotFound,
            2: ProfileNotInEnabledState,
            3: DisallowedByPolicy,
            4: CatBusy,
        }

        exception_class = error_map.get(result, ProfileInteractionException)

        raise exception_class()


class IccidOrAidNotFound(ProfileInteractionException):
    message = "ICCID or AID not found"


class ProfileNotInEnabledState(ProfileInteractionException):
    message = "Profile not in enabled state"


class DisallowedByPolicy(ProfileInteractionException):
    message = "Operation disallowed by policy"


class CatBusy(ProfileInteractionException):
    message = "CAT is busy"
