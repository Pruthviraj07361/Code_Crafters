from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """Identical to DRF's TokenAuthentication, just matching the 'Bearer'
    scheme the frontend sends instead of DRF's default 'Token' scheme."""
    keyword = 'Bearer'
