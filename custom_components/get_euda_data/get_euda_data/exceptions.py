class PyCupraConfigException(Exception):
    """Raised when API client is configured incorrectly"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraConfigException, self).__init__(status)
        self.status = status


class PyCupraAuthenticationException(Exception):
    """Raised when credentials are invalid during authentication"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraAuthenticationException, self).__init__(status)
        self.status = status


class PyCupraAccountLockedException(Exception):
    """Raised when account is locked from too many login attempts"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraAccountLockedException, self).__init__(status)
        self.status = status


class PyCupraTokenExpiredException(Exception):
    """Raised when server reports that the access token has expired"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraTokenExpiredException, self).__init__(status)
        self.status = status


class PyCupraException(Exception):
    """Raised when an unknown error occurs during API interaction"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraException, self).__init__(status)
        self.status = status


class PyCupraEULAException(Exception):
    """Raised when EULA must be accepted before login"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraEULAException, self).__init__(status)
        self.status = status


class PyCupraMarketingConsentException(Exception):
    """Raised when question to marketing consent must be accepted before login"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraMarketingConsentException, self).__init__(status)
        self.status = status


class PyCupraLoginFailedException(Exception):
    """Raised when login fails for an unknown reason"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraLoginFailedException, self).__init__(status)
        self.status = status


class PyCupraInvalidRequestException(Exception):
    """Raised when an unsupported request is made"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraInvalidRequestException, self).__init__(status)
        self.status = status


class PyCupraRequestInProgressException(Exception):
    """Raised when a request fails because another request is already in progress"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraRequestInProgressException, self).__init__(status)
        self.status = status


class PyCupraServiceUnavailable(Exception):
    """Raised when a API is unavailable"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraServiceUnavailable, self).__init__(status)
        self.status = status


class PyCupraEUDAPermissionExpiredException(Exception):
    """Raised when EUDA server reports that the permission is not valid"""

    def __init__(self, status):
        """Initialize exception"""
        super(PyCupraEUDAPermissionExpiredException, self).__init__(status)
        self.status = status

