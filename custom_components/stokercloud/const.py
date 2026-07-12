import voluptuous as vol

from homeassistant.const import CONF_SCAN_INTERVAL, CONF_USERNAME
import homeassistant.helpers.config_validation as cv

DOMAIN = "stokercloud"
DATA_SCHEMA = vol.Schema({vol.Required(CONF_USERNAME): cv.string})

CONF_API_VARIANT = "api_variant"
CONF_SCREEN = "screen"

API_VARIANT_V2 = "v2"
API_VARIANT_V16 = "v16bck"
API_VARIANTS = [API_VARIANT_V2, API_VARIANT_V16]

DEFAULT_API_VARIANT = API_VARIANT_V2
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_SCREEN = (
    "b1,0,b2,5,b3,4,b4,6,b5,12,b6,14,b7,15,b8,16,b9,9,b10,0,"
    "d1,0,d2,4,d3,0,d4,0,d5,0,d6,0,d7,0,d8,0,d9,0,d10,0,"
    "h1,2,h2,3,h3,4,h4,7,h5,8,h6,14,h7,0,h8,0,h9,0,h10,0,"
    "w1,2,w2,3,w3,9,w4,0,w5,0"
)

MANUFACTURER = "NBE"
MODEL = "Stoker cloud boiler"

ALARM = {
    False: ["OK", "mdi:alarm-light-outline"],
    True: ["ALARM", "mdi:alarm-light-outline"],
}

RUNNING = {
    False: ["IDLE", "mdi:radiator"],
    True: ["RUNNING", "mdi:radiator"],
}

LNG_STATE_MAP = {
    "lng_state_0": "Wait a moment",
    "lng_state_1": "Ignition 1",
    "lng_state_2": "Ignition 1",
    "lng_state_3": "Ignition 2",
    "lng_state_4": "Ignition 2",
    "lng_state_5": "Power",
    "lng_state_6": "Pause",
    "lng_state_7": "DHW",
    "lng_state_8": "Temperature error boiler",
    "lng_state_9": "Stopped - temperature reached",
    "lng_state_10": "Summer stop",
    "lng_state_11": "Alarm burner is too hot do not restart before the problem is found !!",
    "lng_state_12": "Plug is disconnected",
    "lng_state_13": "Fault ignition",
    "lng_state_14": "Off",
    "lng_state_15": "Error boiler temp. sensor",
    "lng_state_16": "Error photo sensor",
    "lng_state_17": "Error burner temp. sensor",
    "lng_state_19": "Error on a motor output",
    "lng_state_20": "Error no fire out of pellets",
    "lng_state_22": "Stopped by external temperature",
    "lng_state_23": "Stopped by timer",
    "lng_state_24": "Stopped by external contact",
    "lng_state_25": "Stopped by weather comp.",
    "lng_state_26": "Fail on fan",
    "lng_state_27": "Error no fire adjustment low",
    "lng_state_28": "Door is open",
    "lng_state_29": "Overheat/auger disconnected",
    "lng_state_30": "Stopped by cascade",
    "lng_state_31": "Compressor failure",
    "lng_state_36": "Back pressure high",
}

STATE_STATE = {
    "state_0": ["WAIT_A_MOMENT", "mdi:information"],
    "state_1": ["IGNITION_1", "mdi:information"],
    "state_2": ["IGNITION_1", "mdi:information"],
    "state_3": ["IGNITION_2", "mdi:information"],
    "state_4": ["IGNITION_2", "mdi:information"],
    "state_5": ["POWER", "mdi:information"],
    "state_6": ["PAUSE", "mdi:information"],
    "state_7": ["HOT_WATER", "mdi:information"],
    "state_8": ["TEMPERATURE_ERROR_BOILER", "mdi:information"],
    "state_9": ["STOPPED_TEMPERATURE_REACHED", "mdi:information"],
    "state_10": ["SUMMER_STOP", "mdi:information"],
    "state_11": ["ALARM_BURNER_TOO_HOT", "mdi:information"],
    "state_12": ["PLUG_DISCONNECTED", "mdi:information"],
    "state_13": ["FAULT_IGNITION", "mdi:information"],
    "state_14": ["OFF", "mdi:information"],
    "state_15": ["ERROR_BOILER_TEMP_SENSOR", "mdi:information"],
    "state_16": ["ERROR_PHOTO_SENSOR", "mdi:information"],
    "state_17": ["ERROR_BURNER_TEMP_SENSOR", "mdi:information"],
    "state_19": ["ERROR_MOTOR_OUTPUT", "mdi:information"],
    "state_20": ["ERROR_NO_FIRE_OUT_OF_PELLETS", "mdi:information"],
    "state_22": ["STOPPED_BY_EXTERNAL_TEMPERATURE", "mdi:information"],
    "state_23": ["STOPPED_BY_TIMER", "mdi:information"],
    "state_24": ["STOPPED_BY_EXTERNAL_CONTACT", "mdi:information"],
    "state_25": ["STOPPED_BY_WEATHER_COMP", "mdi:information"],
    "state_26": ["FAIL_ON_FAN", "mdi:information"],
    "state_27": ["ERROR_NO_FIRE_ADJUSTMENT_LOW", "mdi:information"],
    "state_28": ["DOOR_OPEN", "mdi:information"],
    "state_29": ["OVERHEAT_AUGER_DISCONNECTED", "mdi:information"],
    "state_30": ["STOPPED_BY_CASCADE", "mdi:information"],
    "state_31": ["COMPRESSOR_FAILURE", "mdi:information"],
    "state_36": ["BACK_PRESSURE_HIGH", "mdi:information"],
}

INFOMESSAGE = {
    "0": ["No info message", "mdi:information"],
    "13": ["Ash tray full", "mdi:information"],
    "24": ["Hopper content low", "mdi:information"],
}
