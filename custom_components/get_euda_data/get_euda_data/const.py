"""Constants for EUDA library."""

AUTH_OIDCONFIG = "https://identity.vwgroup.io/.well-known/openid-configuration"  # OpenID configuration

# Constants for EUDA connection
EUDA_CLIENT_LIST= {
    "cupra": {
        "CLIENT_ID": "f85e5b69-e3b2-43aa-9c0d-1b7d0e0b576f@apps_vw-dilab_com",
        "SCOPE": "openid profile cars",
        "REDIRECT_URL": "https://eu-data-act.drivesomethinggreater.com/login",
    },
    "seat": {
        "CLIENT_ID": "f85e5b69-e3b2-43aa-9c0d-1b7d0e0b576f@apps_vw-dilab_com",
        "SCOPE": "openid profile cars",
        "REDIRECT_URL": "https://eu-data-act.drivesomethinggreater.com/login",
    },
    "audi": {
        "CLIENT_ID": "cc29b87a-5e9a-4362-aecf-5adea6b01bbb@apps_vw-dilab_com",
        "SCOPE": "openid profile cars",
        "REDIRECT_URL": "https://eu-data-act.drivesomethinggreater.com/login",
    },
    "skoda": {
        "CLIENT_ID": "3ea88bf9-1d4e-4a68-b3ad-4098c1f1d246@apps_vw-dilab_com",
        "SCOPE": "openid profile cars",
        "REDIRECT_URL": "https://eu-data-act.drivesomethinggreater.com/login",
    },
    "volkswagen_passenger_cars": {
        "CLIENT_ID": "9b58543e-1c15-4193-91d5-8a14145bebb0@apps_vw-dilab_com",
        "SCOPE": "openid profile cars",
        "REDIRECT_URL": "https://eu-data-act.drivesomethinggreater.com/login",
    },
}

EUDA_HEADERS_SESSION = {
    "Connection": "keep-alive",
    "Content-Type": "*/*",  #'application/json',
    "Accept-charset": "UTF-8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
    "Referer": "https://eu-data-act.drivesomethinggreater.com/de/en/user.html",
    #'User-ID': '?????', # to be set later
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
}

EUDA_HEADERS_AUTH = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Referer": "https://eu-data-act.drivesomethinggreater.com/de/en/login.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
}

# Urls for EUDA connection
EUDA_AUTH_OIDC = "https://identity.vwgroup.io/oidc/v1/authorize"  # Authorization endpoint for EUDA login
EUDA_AUTH_ISSUER = "https://identity.vwgroup.io"  # Authorization issuer for EUDA login

EUDA_BASE_URL = "https://eu-data-act.drivesomethinggreater.com"
EUDA_API_VEHICLES = "{baseurl}/proxy_api/consent/me/vehicles?viewPosition={viewPos}"  # Endpoint to get vehicles
EUDA_API_FILE_DOWNLOAD = (
    "{baseurl}/proxy_api/euda-apim/datadelivery/vehicles/{vin}/{id}/download"  # Endpoint to download a data file
)
EUDA_API_FILE_LIST = (
    "{baseurl}/proxy_api/euda-apim/datadelivery/vehicles/{vin}/{id}/list"  # Endpoint to read a list of available files
)
EUDA_API_DATACLUSTERS = (
    "{baseurl}/proxy_api/euda-apim/datarequest/vehicles/{vin}/metadata/{type}"  # Endpoint to read data cluster information
)
EUDA_URL_DETAILS = "{baseurl}/content/euda/de/en/user/details?vin={vin}"

EUDA_API_TOKEN = "{baseurl}/libs/granite/csrf/token.json"
EUDA_API_PERMISSION_CHECK = "{baseurl}/services/permissioncheck"
EUDA_API_LOGOUT = "{baseurl}/services/logout"  # still in test

# Keys for Data of the EUDA portal
EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY = "ecd266dd-f536-39c2-a575-352216b87f39"
EUDA_SHORT_TERM_DATA_MILEAGE_KEY = "9f55581a-4fa2-3570-9c9e-b80d210b9a42"
EUDA_SHORT_TERM_DATA_TRAVEL_TIME_KEY = "f0890c07-e62e-32dc-ab3b-80431f070b13"
EUDA_SHORT_TERM_DATA_AVERAGE_ELECTR_ENGINE_CONSUMPTION_KEY = (
    "3b1bdf91-8e59-333a-93ed-f8e5a980bc96"
)
EUDA_SHORT_TERM_DATA_AVERAGE_FUEL_CONSUMPTION_KEY = (
    "a0ee824b-9a53-34ee-8107-3ed94684efa7"
)
EUDA_SHORT_TERM_DATA_AVERAGE_GAS_CONSUMPTION_KEY = (
    "bdf31409-b799-3969-8199-e305082aabf2"
)
EUDA_LONG_TERM_DATA_START_MILEAGE_KEY = "2bfaa641-c972-3816-ae7c-73459bcd673d"
EUDA_LONG_TERM_DATA_MILEAGE_KEY = "f8eba56b-ee3f-3c48-b852-03c9b956053f"
EUDA_LONG_TERM_DATA_TRAVEL_TIME_KEY = "d2ad181b-511a-37d0-8109-e676e68c86b2"
EUDA_LONG_TERM_DATA_AVERAGE_ELECTR_ENGINE_CONSUMPTION_KEY = (
    "79f1709e-028d-3b3a-936e-bbef63b92969"
)
EUDA_LONG_TERM_DATA_AVERAGE_FUEL_CONSUMPTION_KEY = (
    "df531c6f-8897-3236-a760-5975322e7021"
)
EUDA_LONG_TERM_DATA_AVERAGE_GAS_CONSUMPTION_KEY = (
    "a326ae4c-afe8-3929-bf1a-b95ba7107c2f"
)
EUDA_LONG_TERM_DATA_AVERAGE_SPEED_KEY = "77838f59-786a-36fa-b1d4-47217a9fb40e"
EUDA_OUTSIDE_TEMPERATURE_KEY = "6810b781-e54a-35e8-af98-fcdefb54bac6"
EUDA_PARKING_BRAKE_KEY = "f8bbe94d-06e1-3311-bf8f-c0c99cc67d48"
#EUDA_OIL_LEVEL_ADDITIONAL_OIL_LEVEL_KEY = "78e92351-cf56-3c15-96d3-9b63d62ca618"
#EUDA_OIL_LEVEL_ACTUAL_LEVEL_KEY = "a3368611-8c63-3b7d-9d19-148a464c7a7b"

EUDA_DATA_CONVERSION_FLOAT = 0
EUDA_DATA_CONVERSION_INT = 1
EUDA_DATA_CONVERSION_BOOL = 2
EUDA_DATA_CONVERSION_DIVIDE_BY_10 = 3
EUDA_DATA_CONVERSION_KELVIN_TO_CELSIUS = 4
EUDA_DATA_CONVERSION_INT_INVERT = 5


EUDA_DATA_DICT = {
    "outside_temperature": {
        "attr": "outside_temperature",
        "name": "Outside temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "key": "6810b781-e54a-35e8-af98-fcdefb54bac6",
        "conversion": EUDA_DATA_CONVERSION_KELVIN_TO_CELSIUS,
    },
    "outsideTemperatureIndication": {
        "attr": "outside_temperature_indication",
        "name": "Outside temperature indication",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "key": "b871c390-5325-377d-a91f-ea09bc0eff92",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "outdoor_temperature": {
        "attr": "outdoor_temperature",
        "name": "Outdoor temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "key": "b6ea5ae8-53ff-386d-8415-1baa0602bbb6",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "min_temperature": {
        "attr": "min_temperature_battery_module",
        "name": "Min temperature battery module",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "key": "374014c4-2fd5-3d73-ac75-7c949e726f00",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "max_temperature": {
        "attr": "max_temperature_battery_module",
        "name": "Max temperature battery module",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "key": "dc4a4716-2205-352f-802f-8d7d59705c5b",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "boardnetBatteryVoltageIndication": {
        "attr": "boardnet_battery_voltage",
        "name": "Boardnet battery voltage",
        "icon": "mdi:battery",
        "unit": "%",
        "device_class": "battery",
        "key": "c5b624db-6a07-3957-9127-98cee0be6c98",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    " oil_level_actual_level": {
        "attr": "oil_level",
        "name": "Oil level",
        "icon": "mdi:oil",
        "unit": "%",
        #"device_class": "temperature",
        "key": "a3368611-8c63-3b7d-9d19-148a464c7a7b",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "parking_brake": {
        "attr": "parking_brake",
        "name": "Parking brake",
        "icon": "mdi:car-brake-parking",
        #"unit": "%",
        "device_class": "door",
        "key": "f8bbe94d-06e1-3311-bf8f-c0c99cc67d48",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
    "long_term_data_average_speed": {
        "attr": "long_term_average_speed",
        "name": "Last long average speed",
        "icon": "mdi:speedometer",
        "unit": "km/h",
        "device_class": "speed",
        "key": "77838f59-786a-36fa-b1d4-47217a9fb40e",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "long_term_data_average_electr_engine_consumption": {
        "attr": "long_term_average_electric_consumption",
        "name": "Last long average electric consumption",
        "icon": "mdi:car-battery",
        "unit": "kWh/100km",
        "device_class": "energy_distance",
        "key": "79f1709e-028d-3b3a-936e-bbef63b92969",
        "conversion": EUDA_DATA_CONVERSION_DIVIDE_BY_10,
    },
    "long_term_data_average_fuel_consumption": {
        "attr": "long_term_average_fuel_consumption",
        "name": "Last long average fuel consumption",
        "icon": "mdi:fuel",
        "unit": "l/100km",
        #"device_class": "energy_distance",
        "key": "df531c6f-8897-3236-a760-5975322e7021",
        "conversion": EUDA_DATA_CONVERSION_DIVIDE_BY_10,
    },
    "long_term_data_average_gas_consumption": {
        "attr": "long_term_average_gas_consumption",
        "name": "Last long average gas consumption",
        "icon": "mdi:storage-tank",
        "unit": "kg/100km",
        #"device_class": "energy_distance",
        "key": "a326ae4c-afe8-3929-bf1a-b95ba7107c2f",
        "conversion": EUDA_DATA_CONVERSION_DIVIDE_BY_10,
    },
    "long_term_data_travel_time": {
        "attr": "long_term_duration",
        "name": "Last long duration",
        "icon": "mdi:clock",
        "unit": "min",
        "device_class": "duration",
        "key": "d2ad181b-511a-37d0-8109-e676e68c86b2",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "long_term_data_mileage": {
        "attr": "long_term_distance",
        "name": "Last long length",
        "icon": "mdi:map-marker-distance",
        "unit": "km",
        "device_class": "distance",
        "key": "f8eba56b-ee3f-3c48-b852-03c9b956053f",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "short_term_data_average_electr_engine_consumption": {
        "attr": "short_term_average_electric_consumption",
        "name": "Last short average electric consumption",
        "icon": "mdi:car-battery",
        "unit": "kWh/100km",
        "device_class": "energy_distance",
        "key": "3b1bdf91-8e59-333a-93ed-f8e5a980bc96",
        "conversion": EUDA_DATA_CONVERSION_DIVIDE_BY_10,
    },
    "short_term_data_average_fuel_consumption": {
        "attr": "short_term_average_fuel_consumption",
        "name": "Last short average fuel consumption",
        "icon": "mdi:fuel",
        "unit": "l/100km",
        #"device_class": "energy_distance",
        "key": "a0ee824b-9a53-34ee-8107-3ed94684efa7",
        "conversion": EUDA_DATA_CONVERSION_DIVIDE_BY_10,
    },
    "short_term_data_average_gas_consumption": {
        "attr": "short_term_average_gas_consumption",
        "name": "Last short average gas consumption",
        "icon": "mdi:storage-tank",
        "unit": "kg/100km",
        #"device_class": "energy_distance",
        "key": "bdf31409-b799-3969-8199-e305082aabf2",
        "conversion": EUDA_DATA_CONVERSION_DIVIDE_BY_10,
    },
    "short_term_data_travel_time": {
        "attr": "short_term_duration",
        "name": "Last short duration",
        "icon": "mdi:clock",
        "unit": "min",
        "device_class": "duration",
        "key": "f0890c07-e62e-32dc-ab3b-80431f070b13",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "short_term_data_mileage": {
        "attr": "short_term_distance",
        "name": "Last short length",
        "icon": "mdi:map-marker-distance",
        "unit": "km",
        "device_class": "distance",
        "key": "9f55581a-4fa2-3570-9c9e-b80d210b9a42",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "fuel_level_current_level": {
        "attr": "fuel_level",
        "name": "Fuel level",
        "icon": "mdi:fuel",
        "unit": "%",
        #"device_class": "distance",
        "key": "1503760b-5570-3001-8ffc-1bb6f464948e",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "tank_current_level": {
        "attr": "tank_level",
        "name": "Tank level",
        "icon": "mdi:fuel",
        "unit": "%",
        #"device_class": "distance",
        "key": "3ba7c870-d2a7-3383-8a17-e4048a57a583",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "cng_gas_level": {
        "attr": "cng_level",
        "name": "Cng level",
        "icon": "mdi:storage-tank",
        "unit": "%",
        #"device_class": "distance",
        "key": "c129d05d-de28-3490-a74a-27811b5e8e2e",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "state_of_charge": {
        "attr": "battery_level",
        "name": "Battery level",
        "icon": "mdi:battery",
        "unit": "%",
        "device_class": "battery",
        "key": "ae0294b4-1286-3e98-a818-1485b8d88430",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "battery_state_report.soc": {
        "attr": "state_of_charge",
        "name": "State of charge",
        "icon": "mdi:battery",
        "unit": "%",
        "device_class": "battery",
        "key": "506cb83e-f99f-3af3-bbeb-0429b69a78d9",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "settings.target_soc": {
        "attr": "target_state_of_charge",
        "name": "Target state of charge",
        "icon": "mdi:battery",
        "unit": "%",
        "device_class": "battery",
        "key": "b3b04f31-b10e-38aa-b8ad-c0da7c06caea",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "mileage": {
        "attr": "distance",
        "name": "Odometer",
        "icon": "mdi:speedometer",
        "unit": "km",
        "device_class": "distance",
        "key": "41c0805c-43e5-313e-9dfb-356cb8d20f7c",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "mileage_value": {
        "attr": "distance_value",
        "name": "Odometer value",
        "icon": "mdi:speedometer",
        "unit": "km",
        "device_class": "distance",
        "key": "30cc36fd-71ca-3c09-9296-e94ebd47bd2b",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "cruising_range_electric": {
        "attr": "electric_range",
        "name": "Electric range",
        "icon": "mdi:car",
        "unit": "km",
        "device_class": "distance",
        "key": "0ca40e18-0564-3eda-bcc0-7aee9ef44f04",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "cruising_range_combined": {
        "attr": "combined_range",
        "name": "Combined range",
        "icon": "mdi:car",
        "unit": "km",
        "device_class": "distance",
        "key": "153e8c40-4c6c-3c17-a11b-0ecc35d55b81",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "cruising_range_primary_engine": {
        "attr": "primary_engine_range",
        "name": "Primary engine range",
        "icon": "mdi:car",
        "unit": "km",
        "device_class": "distance",
        "key": "55e0d40b-38ed-3cb5-9dcd-6193df6fc493",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "cruising_range_secondary_engine": {
        "attr": "secondary_engine_range",
        "name": "Secondary engine range",
        "icon": "mdi:car",
        "unit": "km",
        "device_class": "distance",
        "key": "3dedefab-8ded-3f5a-907f-d5e9970720bf",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "lock_state": {
        "attr": "doors_locked",
        "name": "Doors locked",
        #"icon": "mdi:car",
        "device_class": "lock",
        "key": "60bc0937-f5a7-3809-9535-9a7942e5dd94",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
    "locked": {
        "attr": "doors_all_locked",
        "name": "Doors all locked",
        #"icon": "mdi:car",
        "device_class": "lock",
        "key": "bd917b58-82bd-3c34-a006-747ca5aec03d",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
    "open_state_front_left_door": {
        "attr": "door_closed_left_front",
        "name": "Door closed left front",
        "icon": "mdi:car-door",
        "device_class": "door",
        "key": "bc9bbc65-8461-30eb-88db-f94148552a20",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
        #"reverse_state": True,
    },
    "open_state_rear_left_door": {
        "attr": "door_closed_left_back",
        "name": "Door closed left back",
        "icon": "mdi:car-door",
        "device_class": "door",
        "key": "bf62dd10-b184-3425-a64c-c50b09420bc3",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
    "open_state_front_right_door": {
        "attr": "door_closed_right_front",
        "name": "Door closed right_front",
        "icon": "mdi:car-door",
        "device_class": "door",
        "key": "0bb971a6-12ef-3382-9b99-5ed0a52f18e9",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
     "open_state_rear_right_door": {
        "attr": "door_closed_right_back",
        "name": "Door closed right back",
        "icon": "mdi:car-door",
        "device_class": "door",
        "key": "60c81e02-4825-3aab-8da8-b8b07f251623",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
     "state_rear_right_door_window_lifter": {
        "attr": "window_closed_right_back",
        "name": "Window closed right back",
        #"icon": "mdi:car-door",
        "device_class": "window",
        "key": "3ef13c1d-7e08-3cf4-b501-a8bda80cff78",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
     "state_front_right_door_window_lifter": {
        "attr": "window_closed_right_front",
        "name": "Window closed right front",
        #"icon": "mdi:car-door",
        "device_class": "window",
        "key": "5fcf7d27-6b76-3de0-9ce9-f207370cdaff",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
     "state_rear_left_door_window_lifter": {
        "attr": "window_closed_left_back",
        "name": "Window closed left back",
        #"icon": "mdi:car-door",
        "device_class": "window",
        "key": "5fb120bb-ab59-38fc-8e03-9ae197c7a1ae",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
     "state_front_left_door_window_lifter": {
        "attr": "window_closed_left_front",
        "name": "Window closed left front",
        #"icon": "mdi:car-door",
        "device_class": "window",
        "key": "60a4f436-5534-32f4-b4cc-b5a88a9d4b91",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
   "charging_state": {
        "attr": "charging_state",
        "name": "Charging state",
        "icon": "mdi:battery",
        "key": "9da735bb-c5d5-39f8-bf53-0fa2a367aa8f",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
   "charging_state_report.current_charge_state": {
        "attr": "current_charge_state",
        "name": "Current charge state",
        "icon": "mdi:battery",
        "key": "a08cca2b-ed42-37bc-b160-d015ce205d3d",
        "conversion": None,
    },
    "energy_flow": {
        "attr": "energy_flow",
        "name": "Energy flow",
        "icon": "mdi:battery",
        "key": "769f98fd-b821-367e-8434-e2c92fc5c52e",
        "conversion": None,
    },
    "charging_mode": {
        "attr": "charging_mode",
        "name": "Charging mode",
        "icon": "mdi:battery",
        "key": "97c7b448-13e7-3266-a6be-7487caf1a354",
        "conversion": None,
    },
    "charging_state_report.charge_mode": {
        "attr": "charge_mode",
        "name": "Charge mode",
        "icon": "mdi:battery",
        "key": "45410f9e-b068-3dc7-9afb-238a2ef7454e",
        "conversion": None,
    },
    "charging_power": {
        "attr": "charging_power",
        "name": "Charging power",
        "icon": "mdi:flash",
        "unit": "kW",
        "device_class": "power",
        "key": "978be4ed-2f7f-32c0-8644-18e7b0dde741",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "battery_state_report.charge_power": {
        "attr": "charge_power",
        "name": "Charge power",
        "icon": "mdi:flash",
        "unit": "kW",
        "device_class": "power",
        "key": "44ed0d61-98c4-36df-b860-b077929a5797",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "battery_state_report.charge_energy": {
        "attr": "charge_energy",
        "name": "Charge energy",
        "icon": "mdi:flash",
        "unit": "kWh",
        #"device_class": "power",
        "key": "e532aed3-190a-3ff0-bfa4-2e05c61c929e",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "battery_state_report.charge_rate": {
        "attr": "charge_rate",
        "name": "Charge rate",
        "icon": "mdi:flash",
        "key": "1efb6000-6b54-366a-9233-d320699687cf",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "battery_state_report.charge_rate_unit": {
        "attr": "charge_rate_unit",
        "name": "Charge rate unit",
        "icon": "mdi:flash",
        "key": "9c83ccaa-5288-38da-9d38-81ef8db469b3",
        "conversion": None,
    },
   "plug_state": {
        "attr": "charging_cable_connected",
        "name": "Charging cable connected",
        "icon": "mdi:battery",
        "device_class": "plug",
        "key": "c111830c-f959-30d2-859a-ea996190d864",
        "conversion": EUDA_DATA_CONVERSION_BOOL,
    },
   "external_power_supply_state": {
        "attr": "external_power_supply_state",
        "name": "External power supply state",
        "icon": "mdi:battery",
        #"unit": "km",
        #"device_class": "plug",
        "key": "a56a4e27-7d8d-3434-a746-4736c3b5a496",
        "conversion": None,
    },
    "maintenance_interval_distance_until_inspection": {
        "attr": "service_inspection_distance",
        "name": "Service inspection distance",
        "icon": "mdi:garage",
        "unit": "km",
        "device_class": "distance",
        "key": "ac86e00b-7fa1-3a59-b481-aa7cfc49b0d9",
        "conversion": EUDA_DATA_CONVERSION_INT_INVERT,
    },
    "maintenance_interval__time_until_inspection": {
        "attr": "service_inspection",
        "name": "Service inspection days",
        "icon": "mdi:garage",
        "unit": "d",
        "device_class": "duration",
        "key": "fd600221-7965-3396-96d7-82a840a2831c",
        "conversion": EUDA_DATA_CONVERSION_INT_INVERT,
    },
    "maintenance_interval_distance_until_oil_change": {
        "attr": "oil_inspection_distance",
        "name": "Oil inspection distance",
        "icon": "mdi:oil",
        "unit": "km",
        "device_class": "distance",
        "key": "d9f36adc-1840-37da-8ca1-7c2d789bcf9e",
        "conversion": EUDA_DATA_CONVERSION_INT_INVERT,
    },
    "maintenance_interval__time_until_oil_change": {
        "attr": "oil_inspection",
        "name": "Oil inspection days",
        "icon": "mdi:oil",
        "unit": "d",
        "device_class": "duration",
        "key": "42b1c47b-e1d1-375f-a76f-32ab0177f03e",
        "conversion": EUDA_DATA_CONVERSION_INT_INVERT,
    },
    "inspectionDistance": {
        "attr": "inspection_distance",
        "name": "Inspection distance",
        "icon": "mdi:garage",
        "unit": "km",
        "device_class": "distance",
        "key": "ea58e713-ef44-3150-9303-edfc519dcdc1",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "energy_contents.maximal_energy_content.physical_value": {
        "attr": "max_energy_content_physical",
        "name": "Max energy content physical",
        "icon": "mdi:battery",
        "unit": "kWh",
        #"device_class": "temperature",
        "key": "09ed1319-7b17-31c6-ba74-817ce91a4c1d",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "energy_contents.current_energy_content.physical_value": {
        "attr": "current_energy_content_physical",
        "name": "Current energy content physical",
        "icon": "mdi:battery",
        "unit": "kWh",
        #"device_class": "temperature",
        "key": "84e64812-6eaa-3477-b587-0c5b02d8446f",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "slope_consumption_values.ascent_slope_consumption.physical_value": {
        "attr": "ascent_slope_consumption_physical",
        "name": "Ascent slope consumption physical",
        "icon": "mdi:battery",
        #"unit": "kWh",
        #"device_class": "temperature",
        "key": "45df4e5a-c2e3-3588-b917-e572ef5ac213",
        "conversion": EUDA_DATA_CONVERSION_FLOAT,
    },
    "parking_light_left": { 
        "attr": "parking_light_left", 
        "name": "Parking light left", 
        "icon": "mdi:car-parking-lights", 
        "device_class": "light", 
        "key": "c7828009-144b-36e9-af38-2c35e7356c34", 
        "conversion": EUDA_DATA_CONVERSION_BOOL, 
    }, 
    "parking_light_right": { 
        "attr": "parking_light_right", 
        "name": "Parking light right", 
        "icon": "mdi:car-parking-lights", 
        "device_class": "light", 
        "key": "0fa69b72-8432-3ef4-a312-cbb2f7861dfc", 
        "conversion": EUDA_DATA_CONVERSION_BOOL, 
    }, 
    "remaining_charging_time": {
        "attr": "charging_time_left",
        "name": "Charging time left",
        "icon": "mdi:battery-charging-100",
        "unit": "min",
        "device_class": "duration",
        "key": "cf28f7d9-6201-30b8-82e5-a461968d30dc",
        "conversion": EUDA_DATA_CONVERSION_INT,
    },
    "other_fields_found": { 
        "attr": "other_fields_found", 
        "name": "Other fields found", 
        "icon": "mdi:help-circle-outline", 
        "key": "00000000-0000-0000-0000-0000", 
        "conversion": None, 
    }, 
    "daily_sum_average_fuel_consumption": {
        "attr": "daily_sum_average_fuel_consumption",
        "name": "Latest daily sum average fuel consumption",
        "icon": "mdi:fuel",
        "unit": "l/100km",
        #"device_class": "energy_distance",
        "key": "10000000-0000-0000-0000-0001",
    },
    "daily_sum_average_electr_engine_consumption": {
        "attr": "daily_sum_average_electric_consumption",
        "name": "Latest daily sum average electric consumption",
        "icon": "mdi:car-battery",
        "unit": "kWh/100km",
        "device_class": "energy_distance",
        "key": "10000000-0000-0000-0000-0002",
    },
    "daily_sum_average_gas_consumption": {
        "attr": "daily_sum_average_gas_consumption",
        "name": "Latest daily sum average gas consumption",
        "icon": "mdi:storage-tank",
        "unit": "kg/100km",
        #"device_class": "energy_distance",
        "key": "10000000-0000-0000-0000-0003",
    },
    "daily_sum_travel_time": {
        "attr": "daily_sum_duration",
        "name": "Latest daily sum duration",
        "icon": "mdi:clock",
        "unit": "min",
        "device_class": "duration",
        "key": "10000000-0000-0000-0000-0004",
    },
    "daily_sum_mileage": {
        "attr": "daily_sum_distance",
        "name": "Latest daily sum length",
        "icon": "mdi:map-marker-distance",
        "unit": "km",
        "device_class": "distance",
        "key": "10000000-0000-0000-0000-0005",
    },
    "monthly_sum_average_fuel_consumption": {
        "attr": "monthly_sum_average_fuel_consumption",
        "name": "Latest monthly sum average fuel consumption",
        "icon": "mdi:fuel",
        "unit": "l/100km",
        #"device_class": "energy_distance",
        "key": "11000000-0000-0000-0000-0001",
    },
    "monthly_sum_average_electr_engine_consumption": {
        "attr": "monthly_sum_average_electric_consumption",
        "name": "Latest monthly sum average electric consumption",
        "icon": "mdi:car-battery",
        "unit": "kWh/100km",
        "device_class": "energy_distance",
        "key": "11000000-0000-0000-0000-0002",
    },
    "monthly_sum_average_gas_consumption": {
        "attr": "monthly_sum_average_gas_consumption",
        "name": "Latest monthly sum average gas consumption",
        "icon": "mdi:storage-tank",
        "unit": "kg/100km",
        #"device_class": "energy_distance",
        "key": "11000000-0000-0000-0000-0003",
    },
    "monthly_sum_travel_time": {
        "attr": "monthly_sum_duration",
        "name": "Latest monthly sum duration",
        "icon": "mdi:clock",
        "unit": "min",
        "device_class": "duration",
        "key": "11000000-0000-0000-0000-0004",
    },
    "monthly_sum_mileage": {
        "attr": "monthly_sum_distance",
        "name": "Latest monthly sum length",
        "icon": "mdi:map-marker-distance",
        "unit": "km",
        "device_class": "distance",
        "key": "11000000-0000-0000-0000-0005",
    },

}

EUDA_DATA_NO_SHOW_SET = (
    EUDA_LONG_TERM_DATA_START_MILEAGE_KEY,
    EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY,
    "0f43f2e7-3556-36a9-8271-a60bc54afad8", # echo
    "7e35b2a4-8f31-30a7-848d-3af7bb1c5e55", # fuel_level__accuracy
    "173589ce-e437-3c6e-a0ec-6df704586fd7", # trueness
    "d7d35c0a-706c-3f28-a61a-c3b002116a25", # tyre_pressure_differential_rear_right
    "a59fa6dd-c0e8-35af-afc0-1f411c33c78c", # tyre_pressure_differential_rear_left
    "351e9e10-b831-391e-9fc4-ccacc8cd3eba", # tyre_pressure_differential_spare_tyre
    "a86e735b-5f04-336a-8dc7-8fb189d02cd2", # tyre_pressure_differential_front_right
    "69729e19-7b1a-3189-8e11-b4b31ab7601a", # tyre_pressure_differential_front_left
)
