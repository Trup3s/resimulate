import base64
import logging

import requests
from osmocom.utils import b2h, h2b

from resimulate.euicc.es.models.authenticate_client import AuthenticateClientResponse
from resimulate.euicc.es.models.bound_profile_package import (
    GetBoundProfilePackageResponse,
)
from resimulate.euicc.es.models.common import asn
from resimulate.euicc.es.models.initiate_authentication import (
    InitiateAuthenticationResponse,
)

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "gsma-rsp-lpad",
    "X-Admin-Protocol": "gsma/rsp/v2.6.0",
}


def initiate_authentication(
    smdpp_address: str, euicc_challenge: str, euicc_info_1: str, verify: bool = False
) -> InitiateAuthenticationResponse:
    """
    Initiate authentication with the eUICC using the provided parameters.

    Args:
        smdpp_address (str): The SMDPP address.
        euicc_challenge (str): The eUICC challenge.
        euicc_info_1 (str): The first part of the eUICC information.

    Returns:
        InitiateAuthenticationResponse: The authentication response.
    """
    path = "gsma/rsp2/es9plus/initiateAuthentication"
    smdpp_url = f"https://{smdpp_address}/{path}"
    b64_euicc_challenge = base64.b64encode(h2b(euicc_challenge)).decode()
    b64_euicc_info_1 = base64.b64encode(asn.encode("EUICCInfo1", euicc_info_1)).decode()

    response = requests.post(
        url=smdpp_url,
        json={
            "smdpAddress": smdpp_address,
            "euiccChallenge": b64_euicc_challenge,
            "euiccInfo1": b64_euicc_info_1,
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
    authenticate_server_response: str,
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
        h2b(authenticate_server_response)
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
    logging.debug(f"Client Authentication result: {authentication_response}")

    if not authentication_response.success():
        raise Exception(
            f"Client Authentication failed: {authentication_response.header.function_execution_status.status_code_data}"
        )

    profile_metadata = asn.decode(
        "StoreMetadataRequest",
        base64.b64decode(authentication_response.profile_metadata),
        check_constraints=True,
    )
    logging.debug(f"Profile Metadata: {profile_metadata}")
    logging.info(
        f"Loading profile {profile_metadata.get('profileName')} ({b2h(profile_metadata.get('iccid'))})"
    )

    return authentication_response


def get_bound_profile_package(
    smdpp_address: str,
    transaction_id: str,
    prepare_download_response: str,
    verify: bool = False,
) -> GetBoundProfilePackageResponse:
    path = "gsma/rsp2/es9plus/getBoundProfilePackage"
    smdpp_url = f"https://{smdpp_address}/{path}"
    b64_prepare_download_response = base64.b64encode(
        h2b(prepare_download_response)
    ).decode()
    data = {
        "transactionId": transaction_id,
        "prepareDownloadResponse": b64_prepare_download_response,
    }

    response = requests.post(
        url=smdpp_url,
        json=data,
        headers=HEADERS,
        verify=verify,
    )
    if response.status_code != 200:
        raise Exception(
            f"Failed to get bound profile package: {response.status_code} - {response.text}"
        )

    bpp_response = GetBoundProfilePackageResponse(**response.json())
    logging.debug(f"Bound Profile Package response: {bpp_response.model_dump_json()}")

    if not bpp_response.success():
        raise Exception(
            f"Get Bound Profile Package failed: {bpp_response.header.function_execution_status.status_code_data}"
        )

    return bpp_response
