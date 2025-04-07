#!/usr/bin/env python3
#
# Simulates a PLC device.
 
 
# Parameters for temperature simulation (these are all 8.8 fixed-point values)
INITIAL_TEMP = int(23 * 256)
MIN_TEMP = int(22.5 * 256)
MAX_TEMP = int(23.5 * 256)
TEMP_CHANGE_MIN = int(0.005 * 256)
TEMP_CHANGE_MAX = int(0.1 * 256)
 
# Parameters for flow simulation, this works the same.
INITIAL_FLOW = int(5 * 256)
MIN_FLOW = int(2 * 256)
MAX_FLOW = int(8 * 256)
FLOW_CHANGE_MIN = int(0.05 * 256)
FLOW_CHANGE_MAX = int(0.1 * 256)
 
 
import asyncio
import logging
import sys
import random
from collections.abc import Callable
from typing import Any

from pymodbus import __version__ as pymodbus_version
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import (
    StartAsyncSerialServer,
    StartAsyncTcpServer,
    StartAsyncTlsServer,
    StartAsyncUdpServer,
)
 
 
_logger = logging.getLogger(__file__)
_logger.setLevel(logging.INFO)
 
 
# Base class for PLC simulation.
# Only need to pass a "context" (list of coils/registers/etc) to define a simulated PLC.
class Server:
    def __init__(self, context):
        # Hardcoded variables relating to connection type
        self.port = 502
        self.comm = "tcp"
        self.host = "0.0.0.0"
        self.framer = "socket"
 
        # Build data storage
        self.context = ModbusServerContext(slaves=context, single=True)
 
        # Imitate a Siemens PLC
        self.identity = ModbusDeviceIdentification(
            info_name={
                "VendorName": "Siemens",
                "ProductCode": "SM",
                "VendorUrl": None,
                "ProductName": "SIMATIC",
                "ModelName": None,
                "MajorMinorRevision": None,
            }
        )
        return self
 
 
    async def run_async_server(self) -> None:
        """Run server."""
        txt = f"### start ASYNC server, listening on {self.port} - {self.comm}"
        _logger.info(txt)
        address = (self.host if self.host else "", self.port if self.port else None)
        await StartAsyncTcpServer(
            context=self.context,  # Data storage
            identity=self.identity,  # server identify
            address=address,  # listen address
            # custom_functions=[],  # allow custom handling
            framer=self.framer,  # The framer strategy to use
            # ignore_missing_slaves=True,  # ignore request to a missing slave
            # broadcast_enable=False,  # treat slave 0 as broadcast address,
            # timeout=1,  # waiting time for request to complete
        )
 
 
# Simulates a PLC that measures & controls temperature
class TemperatureControllerPLC(Server):
    def __init__(self):
        # Single input register, representing the detected temperature.
        ir = ModbusSequentialDataBlock(0x01, [INITIAL_TEMP])
 
        self.datablock = ModbusSlaveContext(
            ir=ir, # Input registers (16-bit, read-only)
        )
 
        super().__init__(self.datablock)
 
        asyncio.create_task(self.update_temperature())
 
    # This runs until program termination. Simulates variation in temperature.
    async def update_temperature(self):
        while True:
            # Read IR value
            temp = self.datablock.getValues(4, 0)[0]
 
            # Randomly fluctuate the temperature
            r = random.randint(0, 1)
            if r == 0 and temp > MIN_TEMP:
                temp -= random.randint(TEMP_CHANGE_MIN, TEMP_CHANGE_MAX)
            elif r == 1 and temp < MAX_TEMP:
                temp += random.randint(TEMP_CHANGE_MIN, TEMP_CHANGE_MAX)
 
            # Write IR value
            self.datablock.setValues(4, 0, [temp])
 
            await asyncio.sleep(0.25)
 
 
# Simulates a valve that records flow rate
class ValvePLC(Server):
    def __init__(self):
        # Single input register, representing the flow rate.
        ir = ModbusSequentialDataBlock(0x01, [INITIAL_FLOW])
 
        self.datablock = ModbusSlaveContext(
            ir=ir, # Input registers (16-bit, read-only)
        )
 
        super().__init__(self.datablock)
 
        asyncio.create_task(self.update_flow())
 
    # This runs until program termination. Simulates variation in temperature.
    async def update_flow(self):
        while True:
            # Read IR value
            flow = self.datablock.getValues(4, 0)[0]
 
            # Randomly fluctuate the flow
            r = random.randint(0, 1)
            if r == 0 and flow > MIN_FLOW:
                flow -= random.randint(FLOW_CHANGE_MIN, FLOW_CHANGE_MAX)
            elif r == 1 and flow < MAX_FLOW:
                flow += random.randint(FLOW_CHANGE_MIN, FLOW_CHANGE_MAX)
 
            # Write IR value
            self.datablock.setValues(4, 0, [flow])
 
            await asyncio.sleep(0.25)
 
 
async def main() -> None:
    if sys.argv[1] == "tempsensor":
        server = TemperatureControllerPLC()
    elif sys.argv[1] == "valve":
        server = ValvePLC()
    await server.run_async_server()
 
if __name__ == "__main__":
    asyncio.run(main(), debug=True)
