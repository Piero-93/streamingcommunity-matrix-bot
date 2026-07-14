# Copyright (C) 2026 The streamingcommunity-matrix-bot contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import asyncio
import logging
from nio import AsyncClient, LoginResponse, InviteMemberEvent, RoomSendResponse
from telegram_source import fetch_latest_domain
from state import load_state, save_state

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_config():
    with open("config.json") as f:
        return json.load(f)


async def main():
    config = load_config()
    server = config["server"]
    user_id = config["user_id"]
    logger.info(f"Logging on {server} with user id {user_id}")
    client = AsyncClient(server, user_id)
    response = await client.login(config["password"])
    if isinstance(response, LoginResponse):
        logger.info("Login successful")
    else:
        logger.error(f"Login failed: {response}")
        return

    async def on_invite(room, event):
        if event.membership != "invite":
            return
        if not load_config().get("allow_new_rooms", True):
            logger.info(f"Ignoring invite to {room.room_id}: new rooms not allowed")
            return
        await client.join(room.room_id)
        await client.room_send(room.room_id, "m.room.message",
            {"msgtype": "m.text", "body": "👋 Hey! I'm the StreamingCommunity bot — I'll keep the latest working link pinned right here, so you never have to go hunting for it again."})
    
    async def poll_loop():
        interval = config["poll_interval_seconds"]
        while True:
            domain = await asyncio.to_thread(fetch_latest_domain)
            if domain is not None and domain != load_state().get("domain"):
                for r in client.rooms:
                    response = await client.room_send(r, "m.room.message", {"msgtype": "m.text", "body": f"🔄 New StreamingCommunity link: https://{domain}"})
                    if isinstance(response, RoomSendResponse):
                        await client.room_put_state(r, "m.room.pinned_events", {"pinned": [response.event_id]})
                    else:
                        logger.error(f"Failed to send message in {r}: {response}")
                save_state({"domain": domain})
            await asyncio.sleep(interval)

    client.add_event_callback(on_invite, InviteMemberEvent)

    await asyncio.gather(
        client.sync_forever(timeout=30000),
        poll_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())
