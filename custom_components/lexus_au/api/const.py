"""Protocol constants captured from the Lexus Australia mobile app."""

AUTH_BASE_URL = "https://login.lexusdriverslogin.com.au"
OPENIDM_BASE_URL = "https://openidm.lexusdriverslogin.com.au"
API_BASE_URL = "https://tmca-oneapi.telematicsct.com.au"

AUTHENTICATE_PATH = (
    "/json/realms/tmca/authenticate?authIndexType=service&authIndexValue=oneapp"
)
AUTHORIZE_PATH = "/oauth2/realms/root/realms/tmca/authorize"
ACCESS_TOKEN_PATH = "/oauth2/realms/root/realms/tmca/access_token"
PASSWORD_CHECK_PATH = "/openidm/endpoint/passwordService?_action=checkPassword"

DEVICE_STATUS_PATH = "/v1/notification/device/status"
REMOTE_STATUS_PATH = "/v1/global/remote/status"
REMOTE_REFRESH_PATH = "/v1/global/remote/refresh-status"
REMOTE_COMMAND_PATH = "/v1/global/remote/command"
VEHICLE_GUID_PATH = "/v2/vehicle/guid"

CLIENT_ID = "oneapp"
REDIRECT_URI = "com.toyota.oneapp:/oauth2Callback"
TOKEN_BASIC_AUTH = "Basic b25lYXBwOm9uZWFwcA=="

# Captured from Lexus AppStore 12.1.1.35. These may need refreshing after app updates.
APP_VERSION = "12.1"
APP_VERSION_FULL = "12.1.1.35"
USER_AGENT = "LexusAppStore/12.1.1.35 CFNetwork/3826.600.41 Darwin/24.6.0"
OS_NAME = "iPadOS"
OS_VERSION = "18.6"
LOCALE = "en-AU"
DEVICE_TIMEZONE = "AEST"
DEVICE_TYPE = "iOS"
DEVICE_MODEL = "iPad"
APP_LABEL = "com.au.lexus.oneapp"
BRAND = "L"
CHANNEL = "ONEAPP"

COMMAND_DOOR_LOCK = "door-lock"
COMMAND_DOOR_UNLOCK = "door-unlock"
COMMAND_ENGINE_START = "engine-start"
COMMAND_ENGINE_STOP = "engine-stop"
COMMAND_HAZARD_ON = "hazard-on"
COMMAND_HAZARD_OFF = "hazard-off"

# AU has already proven to use modern command strings with old-style numeric direction values.
COMMAND_VALUE_ON = 1
COMMAND_VALUE_OFF = 2
