#!/usr/bin/env python3
from __future__ import annotations
 
import os
import asyncio
import logging
import sys
import time
 
 
import pymodbus.client as modbusClient
 
 
# Output logs to file
logging.basicConfig(filename=os.getenv("HOME") + "/plc-log.txt", 
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s'
                    )
# Also output to stderr
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
 
_logger = logging.getLogger(__file__)
_logger.setLevel("DEBUG")
 
def setup_async_client(host) -> modbusClient.ModbusBaseClient:
    """Run client setup."""
    _logger.info(f"Connecting to PLC at {host}...")
    client: modbusClient.ModbusBaseClient | None = None
    client = modbusClient.AsyncModbusTcpClient(
            host,
            port=502,
            # Common optional parameters:
            framer="socket",
            timeout=5,
            retries=3,
            reconnect_delay=1,
            reconnect_delay_max=10,
            #    source_address=("localhost", 0),
            )
    return client
 
 
# Converts an 8.8 fixed-point number to a string, with 2 decimal points.
# This is the format used by the temperature measurement.
def fixed_to_string(v):
    return f'{v / 256:.2f}'
 
 
async def main():
    # Device 1: Temperature sensor
    temp_client = setup_async_client('10.0.2.5')
    await temp_client.connect()
 
    # Device 2: Valve with flow measurements
    valve_client = setup_async_client('10.0.2.8')
    await valve_client.connect()
 
    # Monitor temperature, flow
    while True:
        rr = await temp_client.read_input_registers(0, count=1, slave=1)
        temp = fixed_to_string(rr.registers[0])
        rr = await valve_client.read_input_registers(0, count=1, slave=1)
        flow = fixed_to_string(rr.registers[0])
        _logger.info(f"Temp: {temp}; Flow: {flow}")
        await asyncio.sleep(5.0)
 
    temp_client.close()
 
 
if __name__ == "__main__":
    asyncio.run(main(), debug=True)
