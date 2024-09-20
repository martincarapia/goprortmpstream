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

import sys
import os

# Get the current directory of app.py
current_dir = os.path.dirname(os.path.abspath(__file__))

submodule_path = os.path.join(current_dir, 'OpenGoPro', 
                              'demos', 'python', 'tutorial', 
                              'tutorial_modules')
# Add the submodule path to the Python path
sys.path.append(submodule_path)

# Your app code using the submodule follows here...

import asyncio
import argparse
from typing import Generator, Final

from bleak import BleakClient
from tutorial_modules import GoProUuid, connect_ble, proto, connect_to_access_point, ResponseManager, logger


async def connect_to_server(serveraddr: str) -> None:
    pass

async def main(ssid: str, password: str, serveraddr: str, identifier: str | None = None) -> str:
    manager = ResponseManager()
    try:
        client = await connect_ble(manager.notification_handler, identifier)
        manager.set_client(client)
        await connect_to_access_point(manager, ssid, password)

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
