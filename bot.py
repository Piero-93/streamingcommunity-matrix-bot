import json
import asyncio
import logging
from nio import AsyncClient, LoginResponse, InviteMemberEvent

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

    client.add_event_callback(on_invite, InviteMemberEvent)

    await client.sync_forever(timeout=30000)


if __name__ == "__main__":
    asyncio.run(main())
