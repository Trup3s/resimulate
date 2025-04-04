from resimulate.euicc.es.models.authenticate_client import AuthenticationClientResponse


def authenticate_server(
    authentication_response: AuthenticationClientResponse, matching_id: str, imei: str
) -> str:
    """
    Authenticate the server using the authentication response.

    Args:
        authentication_response (AuthenticationResponse): The authentication response object.
        matching_id (str): The matching ID.
        imei (str): The IMEI.

    Returns:
        str: The authentication result.
    """
