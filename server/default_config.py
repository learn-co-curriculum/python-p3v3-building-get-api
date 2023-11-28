# server/default_config.py
"""Default application settings"""

class DefaultConfig:
    """Default configuration"""
    API_TITLE = "Team API"
    API_VERSION = 1.0
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    PROPAGATE_EXCEPTIONS = True
    DEBUG = True
