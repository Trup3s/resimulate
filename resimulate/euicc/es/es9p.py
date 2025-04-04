import requests

from resimulate.euicc.es.models.authentication_response import (
    AuthenticationResponse,
)


def initiate_authentication(
    smdpp_address: str, euicc_challenge: str, euicc_info_1: str
) -> AuthenticationResponse:
    """
    Initiate authentication with the eUICC using the provided parameters.

    Args:
        smdpp_address (str): The SMDPP address.
        euicc_challenge (str): The eUICC challenge.
        euicc_info_1 (dict): The first part of the eUICC information.

    Returns:
        AuthenticationResponse: The authentication response.
    """
    path = "gsma/rsp2/es9plus/initiateAuthentication"
    smdpp_url = f"https://{smdpp_address}/{path}"
    euicc_challenge = "8rUN4NsUabMHrpnV8TmUgQ=="
    response = requests.post(
        url=smdpp_url,
        json={
            "smdpAddress": smdpp_address,
            "euiccChallenge": euicc_challenge,
            "euiccInfo1": euicc_info_1,
        },
        headers={
            "Content-Type": "application/json",
            "User-Agent": "gsma-rsp-lpad",
            "X-Admin-Protocol": "gsma/rsp/v2.2.0",
        },
        verify=False,
    )
    if response.status_code != 200:
        raise Exception(
            f"Failed to initiate authentication: {response.status_code} - {response.text}"
        )

    authentication_response = AuthenticationResponse(**response.json())

    if not authentication_response.success():
        raise Exception(
            f"Authentication failed: {authentication_response.header.function_execution_status.status_code_data}"
        )

    return authentication_response
