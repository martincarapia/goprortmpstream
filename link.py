# take the connect_as_sta code which will connect the gopro to the desired access point. 

# Kinda following this howto
# https://gopro.github.io/OpenGoPro/ble/features/live_streaming.html


"""
Put the camera into Station Mode and connect it to an access point

Use Set Livestream Mode to configure livestreaming.

Poll for Livestream Status until the camera indicates it is ready

Set the shutter to begin live streaming

Unset the shutter to stop live streaming
"""

import os
import sys

# Get the current directory of link.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to tutorial_modules
submodule_path = os.path.join(
    current_dir, 
    'OpenGoPro', 'demos', 'python', 'tutorial'
)

# Add the submodule path to sys.path before importing
sys.path.append(submodule_path)


import asyncio
import argparse
from typing import Generator, Final

from bleak import BleakClient
from tutorial_modules import GoProUuid, connect_ble, proto, connect_to_access_point, ResponseManager, logger

async def set_shutter(manager: ResponseManager):
    """Set shutter in order to start/stop live stream

    Args: 
        manager (ResponseManager): manager used to perform the operation

    Raises:
        RuntimeError: Received unexpected response.

    Returns: 
        Not sure what yet
    """
    logger.info(msg="Setting the shutter on")

    request = bytes([3, 1, 1, 1])
    logger.debug(f"Writing to {GoProUuid.COMMAND_REQ_UUID}: {request.hex(':')}")
    await manager.client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, request, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id != 0x72:
            raise RuntimeError("Only expect to receive Feature ID 0x72 responses after scan request")
        if response.action_id == 0x73:  # Initial Scan Response
            manager.assert_generic_protobuf_success(response.data)
        else:
            raise RuntimeError("Only expect to receive Action ID 0x72 or 0x73 responses after scan request")
    raise RuntimeError("Loop should not exit without return")
async def set_live_stream_mode(manager: ResponseManager, serveraddr: str) -> None:
    """Configure Live Streaming

    Args: 
        manager (ResponseManager): manager used to perform the operation
        serveraddr: RTMP Server Address on the local network

    Raises:
        RuntimeError: Received unexpected response.

    Returns: 
        Not sure what yet
    """

    logger.info(msg="Setting Live Stream Mode")

    start_live_stream_configure = bytearray(
        [
            0xF1,  # Feature ID
            0x79,  # Action ID
            *proto.RequestSetLiveStreamMode(url=serveraddr, encode=False).SerializePartialToString(),
        ]
    )
    start_live_stream_configure.insert(0, len(start_live_stream_configure))

    # Send the livestream configure request
    logger.debug(f"Writing: {start_live_stream_configure.hex(':')}")
    await manager.client.write_gatt_char(GoProUuid.COMMAND_REQ_UUID.value, start_live_stream_configure, response=True)
    while response := await manager.get_next_response_as_protobuf():
        if response.feature_id != 0xF1:
            raise RuntimeError("Only expect to receive Feature ID 0xF1 responses after scan request")
        if response.action_id == 0xF9:  # Initial Scan Response
            manager.assert_generic_protobuf_success(response.data)
        else:
            raise RuntimeError("Only expect to receive Action ID 0xF1 or 0xF9 responses after scan request")
    raise RuntimeError("Loop should not exit without return")

async def main(ssid: str, password: str, serveraddr: str, identifier: str | None = None) -> str:
    manager = ResponseManager()
    try:
        client = await connect_ble(manager.notification_handler, identifier)
        manager.set_client(client)
        await connect_to_access_point(manager, ssid, password)
        await set_live_stream_mode(manager, serveraddr)

        await asyncio.sleep(2)

        await set_shutter(manager)



    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error(repr(exc))
    finally:
        if manager.is_initialized:
            await manager.client.disconnect()
    return "it works?"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to a specified access point and starts streaming the gopro to specified RTMP server.")
    parser.add_argument("ssid", type=str, help="SSID of network to connect to")
    parser.add_argument("password", type=str, help="Password of network to connect to")
    parser.add_argument("serveraddr", type=str, help="RTMP Server Address on the local network that the camera will livestream to. Make sure to include the stream key on the end of the address. For example: rtmp://127.0.0.1/live/EXAMPLE")
    parser.add_argument(
        "-i",
        "--identifier",
        type=str,
        help="Last 4 digits of GoPro serial number, which is the last 4 digits of the default camera SSID. If not used, first discovered GoPro will be connected to",
        default=None,
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.ssid, args.password, args.serveraddr, args.identifier,))
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(e)
        sys.exit(-1)
    else:
        sys.exit(0)
