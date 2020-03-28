"""
Interface module for Lutron Caseta Smart Bridge PRO and Ra2 Select Main Repeater.

This module uses the Telnet interface which must be
enabled through the integration menu in the mobile app.
"""

import asyncio
import json
import logging
import re
from enum import IntEnum

READ_SIZE = 1024
DEFAULT_USER = b"lutron"
DEFAULT_PASSWORD = b"integration"
CASETA_RE = re.compile(b"~([A-Z]+),([0-9.]+),([0-9.]+),([0-9.]+)\r\n")
CONF_ID = "id"
CONF_NAME = "name"
CONF_TYPE = "type"
CONF_SCENE_ID = "scene_id"
CONF_AREA_NAME = "area_name"
CONF_BUTTONS = "buttons"

_LOGGER = logging.getLogger(__name__)


async def async_load_integration_report(fname):
    """Process a JSON integration report and return a list of devices.

    Each returned device will have an 'id', 'name', 'type' and optionally
    a list of button IDs under 'buttons' for remotes
    and an 'area_name' attribute if the device is assigned
    to an area.
    """
    devices = []
    with open(fname, encoding="utf-8") as conf_file:
        integration_report = json.load(conf_file)
        # _LOGGER.debug(integration)
        if "LIPIdList" in integration_report:
            # lights and switches are in Zones
            if "Zones" in integration_report["LIPIdList"]:
                _process_zones(devices, integration_report)
            # remotes are in Devices, except ID 1 which is the bridge itself
            if "Devices" in integration_report["LIPIdList"]:
                for device in integration_report["LIPIdList"]["Devices"]:
                    # extract scenes from integration ID 1 - the smart bridge
                    if device["ID"] == 1 and "Buttons" in device:
                        _process_scenes(devices, device)
                    elif device["ID"] != 1 and "Buttons" in device:
                        device_obj = {
                            CONF_ID: device["ID"],
                            CONF_NAME: device["Name"],
                            CONF_TYPE: "sensor",
                            CONF_BUTTONS: [b["Number"] for b in device["Buttons"]],
                        }
                        if "Area" in device and "Name" in device["Area"]:
                            device_obj[CONF_AREA_NAME] = device["Area"]["Name"]
                        devices.append(device_obj)
        else:
            _LOGGER.warning(
                "'LIPIdList' not found in the Integration Report. No devices will be loaded."
            )
    return devices


def _process_zones(devices, integration_report):
    """Process zones and append devices."""
    for zone in integration_report["LIPIdList"]["Zones"]:
        # _LOGGER.debug(zone)
        device_obj = {CONF_ID: zone["ID"], CONF_NAME: zone["Name"], CONF_TYPE: "light"}
        if "Area" in zone and "Name" in zone["Area"]:
            device_obj[CONF_AREA_NAME] = zone["Area"]["Name"]
        devices.append(device_obj)


def _process_scenes(devices, device):
    """Process scenes and append devices."""
    for button in device["Buttons"]:
        if not button["Name"].startswith("Button "):
            _LOGGER.info("Found scene %d, %s", button["Number"], button["Name"])
            devices.append(
                {
                    CONF_ID: device["ID"],
                    CONF_NAME: button["Name"],
                    CONF_SCENE_ID: button["Number"],
                    CONF_TYPE: "scene",
                }
            )


# pylint: disable=too-many-instance-attributes
class Casetify:
    """Async class to communicate with Lutron bridge."""

    OUTPUT = "OUTPUT"
    DEVICE = "DEVICE"

    class Action(IntEnum):
        """Action values."""

        SET = 1
        RAISING = 2
        LOWERING = 3
        STOP = 4

    class Button(IntEnum):
        """Button values."""

        PRESS = 3
        RELEASE = 4

    class State(IntEnum):
        """State values."""

        Closed = 1
        Opening = 2
        Opened = 3

    def __init__(self):
        """Initialize Casetify."""
        self._read_buffer = b""
        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._state = Casetify.State.Closed
        self._host = None
        self._port = 23
        self._username = DEFAULT_USER
        self._password = DEFAULT_PASSWORD
        self.reader, self.writer = None, None

    def is_connected(self):
        """Return if the connection is open."""
        return self._state == Casetify.State.Opened

    async def open(
        self, host, port=23, username=DEFAULT_USER, password=DEFAULT_PASSWORD
    ):
        """Open a Telnet connection to Lutron bridge."""
        async with self._read_lock:
            async with self._write_lock:
                if self._state != Casetify.State.Closed:
                    return
                self._state = Casetify.State.Opening

                self._host = host
                self._port = port
                self._username = username
                self._password = password

                # open connection
                try:
                    connection = await asyncio.open_connection(host, port)
                except OSError as err:
                    _LOGGER.warning(
                        "Error opening connection to Lutron bridge: %s", err
                    )
                    self._state = Casetify.State.Closed
                    return

                self.reader = connection[0]
                self.writer = connection[1]

                # do login
                await self._read_until(b"login: ")
                self.writer.write(username + b"\r\n")
                await self.writer.drain()
                await self._read_until(b"password: ")
                self.writer.write(password + b"\r\n")
                await self.writer.drain()
                await self._read_until(b"GNET> ")

                self._state = Casetify.State.Opened

    async def _read_until(self, value):
        """Read until a given value is reached."""
        while True:
            if hasattr(value, "search"):
                # assume regular expression
                match = value.search(self._read_buffer)
                if match:
                    self._read_buffer = self._read_buffer[match.end() :]
                    return match
            else:
                where = self._read_buffer.find(value)
                if where != -1:
                    self._read_buffer = self._read_buffer[where + len(value) :]
                    return True
            try:
                read_data = await self.reader.read(READ_SIZE)
                if not read_data:
                    _LOGGER.warning("Empty read from Lutron bridge (clean disconnect)")
                    return False
                self._read_buffer += read_data
            except OSError as err:
                _LOGGER.warning("Error reading from Lutron bridge: %s", err)
                return False

    async def read(self):
        """Return a list of values read from the Telnet interface."""
        async with self._read_lock:
            if self._state != Casetify.State.Opened:
                return None, None, None, None
            match = await self._read_until(CASETA_RE)
            if match is not False:
                # 1 = mode, 2 = integration number,
                # 3 = action number, 4 = value
                try:
                    return (
                        match.group(1).decode("utf-8"),
                        int(match.group(2)),
                        int(match.group(3)),
                        float(match.group(4)),
                    )
                except ValueError:
                    print("Exception in ", match.group(0))
        if match is False:
            # attempt to reconnect
            _LOGGER.info("Reconnecting to Lutron bridge %s", self._host)
            self._state = Casetify.State.Closed
            await self.open(self._host, self._port, self._username, self._password)
        return None, None, None, None

    async def write(self, mode, integration, action, *args, value=None):
        """Write a list of values out to the Telnet interface."""
        if hasattr(action, "value"):
            action = action.value
        async with self._write_lock:
            if self._state != Casetify.State.Opened:
                return
            data = "#{},{},{}".format(mode, integration, action)
            if value is not None:
                data += ",{}".format(value)
            for arg in args:
                if arg is not None:
                    data += ",{}".format(arg)
            try:
                self.writer.write((data + "\r\n").encode())
                await self.writer.drain()
            except OSError as err:
                _LOGGER.warning("Error writing out to the Lutron bridge: %s", err)

    async def query(self, mode, integration, action):
        """Query a device to get its current state."""
        if hasattr(action, "value"):
            action = action.value
        _LOGGER.debug(
            "Sending query %s, integration %s, action %s", mode, integration, action
        )
        async with self._write_lock:
            if self._state != Casetify.State.Opened:
                return
            self.writer.write(
                "?{},{},{}\r\n".format(mode, integration, action).encode()
            )
            await self.writer.drain()

    async def ping(self):
        """Ping the interface to keep the connection alive."""
        async with self._write_lock:
            if self._state != Casetify.State.Opened:
                return
            self.writer.write(b"?SYSTEM,10\r\n")
            await self.writer.drain()
