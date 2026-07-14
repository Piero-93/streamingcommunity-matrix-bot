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
from nio import (
    AsyncClient,
    LoginResponse,
    InviteMemberEvent,
    RoomSendResponse,
    RoomPutStateResponse,
    RoomGetStateEventResponse,
    RoomGetEventResponse,
)
from telegram_source import fetch_latest_domain
from state import load_state, save_state

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_config():
    """Load the bot configuration (server, credentials, poll settings) from config.json."""
    with open("config.json") as f:
        return json.load(f)


async def main():
    """Log in, then run the Matrix sync loop and the domain-polling loop together."""
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
        """Auto-join rooms the bot is invited to (if allowed) and post a welcome message."""
        if event.membership != "invite":
            return
        if not load_config().get("allow_new_rooms", True):
            logger.info(f"Ignoring invite to {room.room_id}: new rooms not allowed")
            return
        await client.join(room.room_id)
        await client.room_send(room.room_id, "m.room.message",
            {"msgtype": "m.text", "body": "👋 Hey! I'm the StreamingCommunity bot — I'll keep the latest working link pinned right here, so you never have to go hunting for it again."})
    
    async def update_pins(room_id, old_event_id, new_event_id):
        """Unpin the bot's previous link (if any), pin the new one, keep other pins."""
        current = await client.room_get_state_event(room_id, "m.room.pinned_events")
        if isinstance(current, RoomGetStateEventResponse):
            pinned = list(current.content.get("pinned", []))
        else:
            pinned = []
        if old_event_id in pinned:
            pinned.remove(old_event_id)
        if new_event_id not in pinned:
            pinned.append(new_event_id)
        return await client.room_put_state(room_id, "m.room.pinned_events", {"pinned": pinned})

    async def check_pinned_link(room_id, event_id):
        """Check the bot's link on the server. Returns 'ok', 'unpinned' or 'gone'."""
        event = await client.room_get_event(room_id, event_id)
        if not isinstance(event, RoomGetEventResponse) or getattr(event.event, "body", None) is None:
            return "gone"  # message deleted/redacted or not retrievable
        pins = await client.room_get_state_event(room_id, "m.room.pinned_events")
        pinned = pins.content.get("pinned", []) if isinstance(pins, RoomGetStateEventResponse) else []
        return "ok" if event_id in pinned else "unpinned"

    async def poll_loop():
        """Periodically fetch the latest domain and, per room, send+pin it once when it changes."""
        interval = config["poll_interval_seconds"]
        verify = config.get("verify_pinned_link", False)
        # Wait for the first sync so client.rooms is populated before we act on it
        # (otherwise the first cycle would see no rooms and prune all saved state).
        await client.synced.wait()
        while True:
            domain = await asyncio.to_thread(fetch_latest_domain)
            if domain is not None:
                state = load_state()
                rooms_state = state.get("rooms", {})
                for r in client.rooms:
                    room = client.rooms[r]
                    room_label = f"{room.display_name} ({r})"
                    info = rooms_state.get(r, {})
                    # Skip rooms where the bot can't post (e.g. server/system rooms like the matrix.org official account).
                    if not room.power_levels.can_user_send_message(room.own_user_id):
                        logger.debug(f"Skipping {room_label}: no permission to send messages")
                        continue
                    # Optionally re-check on the server that a previously posted link is still there and pinned.
                    if verify and info.get("domain") == domain and info.get("event_id") and info.get("pinned_event_id") == info["event_id"]:
                        status = await check_pinned_link(r, info["event_id"])
                        if status == "gone":
                            logger.info(f"Bot link missing in {room_label}, re-posting")
                            info = {}
                            rooms_state[r] = info
                        elif status == "unpinned":
                            logger.info(f"Bot link unpinned in {room_label}, re-pinning")
                            info["pinned_event_id"] = None
                            rooms_state[r] = info
                    # Send the message only if this room hasn't received the current link yet.
                    if info.get("domain") != domain:
                        response = await client.room_send(r, "m.room.message", {"msgtype": "m.text", "body": f"🔄 New StreamingCommunity link: https://{domain}"})
                        if not isinstance(response, RoomSendResponse):
                            logger.error(f"Failed to send message in {room_label}: {response}")
                            continue
                        info["domain"] = domain
                        info["event_id"] = response.event_id
                        rooms_state[r] = info  # record the send even if the pin below fails
                    # Pin the current link if it isn't already pinned (also retries a previously failed pin).
                    if info.get("pinned_event_id") != info.get("event_id"):
                        if not room.power_levels.can_user_send_state(room.own_user_id, "m.room.pinned_events"):
                            logger.debug(f"Skipping pin in {room_label}: no permission to manage pinned events")
                        else:
                            pin_response = await update_pins(r, info.get("pinned_event_id"), info["event_id"])
                            if isinstance(pin_response, RoomPutStateResponse):
                                logger.info(f"Pinned message in {room_label}")
                                info["pinned_event_id"] = info["event_id"]
                                rooms_state[r] = info
                            else:
                                logger.error(f"Failed to pin message in {room_label}: {pin_response}")
                # Drop state for rooms the bot is no longer a member of (kicked/left), so a
                # future re-join is treated as fresh instead of "already sent".
                for stale in [rid for rid in rooms_state if rid not in client.rooms]:
                    logger.info(f"Removing state for room no longer joined: {stale}")
                    del rooms_state[stale]
                state["rooms"] = rooms_state
                state["domain"] = domain
                save_state(state)
            await asyncio.sleep(interval)

    client.add_event_callback(on_invite, InviteMemberEvent)

    try:
        await asyncio.gather(
            client.sync_forever(timeout=30000),
            poll_loop(),
        )
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down")
