from resimulate.euicc.es.models.authentication_response import AuthenticationResponse


def authenticate_server(
    authentication_response: AuthenticationResponse, matching_id: str, imei: str
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
