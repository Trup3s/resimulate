import base64
import binascii
import logging

import requests

from resimulate.euicc.es.models.authenticate_client import AuthenticateClientResponse
from resimulate.euicc.es.models.authenticate_server import AuthenticateServerResponse
from resimulate.euicc.es.models.initiate_authentication import (
    InitiateAuthenticationResponse,
)

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "gsma-rsp-lpad",
    "X-Admin-Protocol": "gsma/rsp/v2.2.0",
}


def initiate_authentication(
    smdpp_address: str, euicc_challenge: str, euicc_info_1: str, verify: bool = False
) -> InitiateAuthenticationResponse:
    """
    Initiate authentication with the eUICC using the provided parameters.

    Args:
        smdpp_address (str): The SMDPP address.
        euicc_challenge (str): The eUICC challenge.
        euicc_info_1 (dict): The first part of the eUICC information.

    Returns:
        InitiateAuthenticationResponse: The authentication response.
    """
    path = "gsma/rsp2/es9plus/initiateAuthentication"
    smdpp_url = f"https://{smdpp_address}/{path}"
    b64_euicc_challenge = base64.b64encode(binascii.unhexlify(euicc_challenge)).decode()

    response = requests.post(
        url=smdpp_url,
        json={
            "smdpAddress": smdpp_address,
            "euiccChallenge": b64_euicc_challenge,
            "euiccInfo1": euicc_info_1,
        },
        headers=HEADERS,
        verify=verify,
    )
    if response.status_code != 200:
        raise Exception(
            f"Failed to initiate authentication: {response.status_code} - {response.text}"
        )

    authentication_response = InitiateAuthenticationResponse(**response.json())

    if not authentication_response.success():
        raise Exception(
            f"Initiate Authentication failed: {authentication_response.header.function_execution_status.status_code_data}"
        )

    logging.debug(
        f"Initiate Authentication response: {authentication_response.model_dump_json()}"
    )

    return authentication_response


def authenticate_client(
    smdpp_address: str,
    transaction_id: str,
    authenticate_server_response: AuthenticateServerResponse,
    verify: bool = False,
) -> AuthenticateClientResponse:
    """
    Authenticate the client using the server response.

    Args:
        smdpp_address (str): The SMDPP address.
        authenticate_server_response (str): The base64 encoded server response.

    Returns:
        AuthenticateClientResponse: The authentication result.
    """
    path = "gsma/rsp2/es9plus/authenticateClient"
    smdpp_url = f"https://{smdpp_address}/{path}"
    b64_authenticate_server = base64.b64encode(
        authenticate_server_response.to_tlv()
    ).decode()
    data = {
        "transactionId": transaction_id,
        "authenticateServerResponse": b64_authenticate_server,
    }

    logging.debug(f"AuthenticateClientRequest: {data}")

    response = requests.post(
        url=smdpp_url,
        json=data,
        headers=HEADERS,
        verify=verify,
    )
    if response.status_code != 200:
        raise Exception(
            f"Failed to authenticate client: {response.status_code} - {response.text}"
        )

    authentication_response = AuthenticateClientResponse(**response.json())

    if not authentication_response.success():
        raise Exception(
            f"Client Authentication failed: {authentication_response.header.function_execution_status.status_code_data}"
        )

    logging.debug(f"Client Authentication result: {authentication_response}")

    return authentication_response
