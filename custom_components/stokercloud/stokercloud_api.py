import decimal
from enum import Enum
import json
import logging
import re
import time
from urllib.parse import urlencode, urljoin

import aiohttp

# from stokercloud.controller_data import ControllerData

logger = logging.getLogger(__name__)


def _sanitize_alias(value) -> str:
    alias = re.sub(r"[^0-9A-Za-z]+", "_", str(value)).strip("_")
    return alias.lower()


class TokenInvalid(Exception):
    pass


class Client:
    BASE_URL = "https://stokercloud.dk/"

    def __init__(
        self,
        name: str,
        password: str = None,
        cache_time_seconds: int = 10,
        api_variant: str = "v2",
        screen: str | None = None,
    ):
        self.name = name
        self.password = password
        self.token = None
        self.state = None
        self.last_fetch = None
        self.cache_time_seconds = cache_time_seconds
        self.api_variant = api_variant
        self.screen = screen
        if self.api_variant == "v16bck":
            self._read_prefix = "v16bck/dataout2"
            self._write_prefix = "v16bckbeta/dataout2"
        else:
            self._read_prefix = "v2/dataout2"
            self._write_prefix = "v2/dataout2"

    @staticmethod
    def _token_expired_payload(data):
        if not isinstance(data, (dict, list)):
            return False
        return "tokenexpired" in json.dumps(data).lower()

    def _build_url(self, path: str, params: dict | None = None, include_token: bool = True):
        query: dict = {}
        if params:
            query.update(params)
        if include_token:
            if self.token is None:
                raise TokenInvalid()
            query["token"] = self.token

        if query:
            return urljoin(self.BASE_URL, f"{path}?{urlencode(query)}")
        return urljoin(self.BASE_URL, path)

    async def refresh_token(self):
        async with aiohttp.ClientSession() as session:
            url = self._build_url(
                f"{self._read_prefix}/login.php",
                {
                    "user": self.name,
                    "password": self.password,
                },
                include_token=False,
            )
            async with session.get(url) as response:
                data = await response.json()
                self.token = data["token"]  # actual token
                self.state = data["credentials"]  # readonly

    async def make_request(self, path, params: dict | None = None, retries: int = 1):
        if self.token is None:
            await self.refresh_token()

        absolute_url = self._build_url(path, params=params)
        logger.debug(absolute_url)

        async with aiohttp.ClientSession() as session:
            async with session.get(absolute_url) as response:
                data = await response.json()

        if self._token_expired_payload(data):
            if retries <= 0:
                raise TokenInvalid("Token expired and reauth failed")
            await self.refresh_token()
            return await self.make_request(path, params=params, retries=retries - 1)

        return data

    async def get_controller_data(self):
        params = {}
        if self.api_variant == "v16bck" and self.screen:
            params["screen"] = self.screen
        self.cached_data = await self.make_request(
            f"{self._read_prefix}/controllerdata2.php", params=params
        )
        self.last_fetch = time.time()

    async def controller_data(self):
        if (
            not self.last_fetch
            or (time.time() - self.last_fetch) > self.cache_time_seconds
        ):
            await self.get_controller_data()
        return ControllerData(self.cached_data)

    async def controller_data_json(self):
        if (
            not self.last_fetch
            or (time.time() - self.last_fetch) > self.cache_time_seconds
        ):
            await self.get_controller_data()
        return self.flatten_json(self.cached_data)

    async def update_controller_value(self, menu, name, value):
        res = await self.make_request(
            f"{self._write_prefix}/updatevalue.php",
            params={
                "menu": menu,
                "name": name,
                "value": value,
            },
        )

        return res.get("updated_value", value)

    def flatten_json(self, jsonIn):
        out = {}

        def flatten(x, name=""):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + "_")
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + "_")
                    if isinstance(a, dict) and "id" in a:
                        alias = _sanitize_alias(a["id"])
                        if alias:
                            for field, value in a.items():
                                if isinstance(value, (dict, list)):
                                    continue
                                out[f"{name}byid_{alias}_{field}"] = value
                                out[f"{name}{alias}_{field}"] = value
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(jsonIn)
        return out


class NotConnectedException(Exception):
    pass


class PowerState(Enum):
    ON = 1
    OFF = 0


class Unit(Enum):
    KWH = "kwh"
    PERCENT = "pct"
    DEGREE = "deg"
    KILO_GRAM = "kg"
    GRAM = "g"


class State(Enum):
    POWER = "state_5"
    HOT_WATER = "state_7"
    IGNITION_1 = "state_2"
    IGNITION_2 = "state_4"
    FAULT_IGNITION = "state_13"
    OFF = "state_14"


STATE_BY_VALUE = {key.value: key for key in State}


class Value:
    def __init__(self, value, unit):
        self.value = decimal.Decimal(value) / 10
        self.unit = unit

    def __eq__(self, other):
        if not isinstance(other, Value):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.value == other.value and self.unit == other.unit

    def __repr__(self):
        return "%s %s" % (self.value, self.unit)

    # def get_from_list_by_key(lst, key, value):
    #     for itm in lst:
    #         if itm.get(key) == value:
    #             return itm


class ControllerData:
    def __init__(self, data):
        if data["notconnected"] != 0:
            raise NotConnectedException("Furnace/boiler not connected to StokerCloud")
        self.data = data

    def get_sub_item(self, submenu, _id):
        return get_from_list_by_key(self.data[submenu], "id", _id)

    @property
    def alarm(self):
        return {0: PowerState.OFF, 1: PowerState.ON}.get(
            self.data["miscdata"].get("alarm")
        )

    @property
    def running(self):
        return {0: PowerState.OFF, 1: PowerState.ON}.get(
            self.data["miscdata"].get("running")
        )

    @property
    def serial_number(self):
        return self.data["serial"]

    @property
    def boiler_temperature_current(self):
        return Value(self.get_sub_item("frontdata", "boilertemp")["value"], Unit.DEGREE)

    @property
    def boiler_temperature_requested(self):
        return Value(
            self.get_sub_item("frontdata", "-wantedboilertemp")["value"], Unit.DEGREE
        )

    @property
    def boiler_kwh(self):
        return Value(self.get_sub_item("boilerdata", "5")["value"], Unit.KWH)

    @property
    def state(self):
        return STATE_BY_VALUE.get(self.data["miscdata"]["state"]["value"])

    @property
    def hotwater_temperature_current(self):
        return Value(self.get_sub_item("frontdata", "dhw")["value"], Unit.DEGREE)

    @property
    def hotwater_temperature_requested(self):
        return Value(self.get_sub_item("frontdata", "dhwwanted")["value"], Unit.DEGREE)

    @property
    def consumption_total(self):
        return Value(self.get_sub_item("hopperdata", "4")["value"], Unit.KILO_GRAM)

    @property
    def consumption_day(self):
        return Value(self.get_sub_item("hopperdata", "3")["value"], Unit.KILO_GRAM)
