# streamingcommunity-matrix-bot

A Matrix bot that keeps the latest working StreamingCommunity link pinned in your
rooms. StreamingCommunity changes its domain periodically (legal blocks/takedowns),
so the bot resolves the current one and shares it automatically.

## Features

- **Resolves the current domain** by scraping the public Telegram channel
  `t.me/s/Streaming_community_sito` (no authentication required) and verifies it
  responds before using it.
- **Multi-room with auto-join**: anyone can invite the bot to their room; it
  joins automatically (can be disabled via `allow_new_rooms`), posts a welcome
  message, and then sends and pins the current link right away instead of waiting
  for the next poll cycle.
- **Announces new links**: it periodically polls for the latest domain and, when
  it changes, sends the new link to each room — once per room (it won't re-send
  the same link, even across restarts).
- **Keeps the link pinned**: it pins the newest link and unpins the previous one
  it had pinned, leaving any other pinned messages in the room untouched. A pin
  that fails (e.g. due to permissions) is retried on the next cycle without
  re-sending the message — and as soon as the bot is granted pin rights it pins
  immediately, without waiting for that cycle (see *Required Matrix permissions*).
- **Optional self-healing** (`verify_pinned_link`): when enabled, on every cycle
  it re-checks on the server that its link is still present and pinned. If the
  message was unpinned it re-pins it; if it was deleted it re-posts and pins a
  fresh one. Disabled by default (it adds an extra request per room each cycle).
- **Skips rooms it can't post in**: rooms where the bot lacks permission to send
  (e.g. the matrix.org official/system room) are skipped instead of erroring.
- **Cleans up after itself**: when the bot is removed from (or leaves) a room, its
  saved state for that room is dropped, so if it's ever re-invited the room is
  treated as fresh.

## Setup

1. Create and activate a virtual environment, then install dependencies:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate        # fish: source .venv/bin/activate.fish
   pip install -r requirements.txt
   ```
2. Create a `config.json` (not versioned) with your bot account and settings:
   ```json
   {
     "server": "https://matrix.org",
     "user_id": "@yourbot:matrix.org",
     "password": "…",
     "poll_interval_seconds": 300,
     "allow_new_rooms": true,
     "verify_pinned_link": false
   }
   ```

| Key                     | Type    | What it does                                                                                                                                                                                       |
| -------------------------| ---------| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `server`                | string  | Base URL of the Matrix homeserver the bot logs in to (e.g. `https://matrix.org`).                                                                                                                  |
| `user_id`               | string  | Full Matrix ID of the bot account, in the form `@name:server`.                                                                                                                                     |
| `password`              | string  | Password for the bot account, used to log in. Keep it secret — `config.json` is git-ignored.                                                                                                       |
| `poll_interval_seconds` | number  | How often (in seconds) the bot checks for a new domain. Use a large value in production (e.g. `3600`); small values are only for testing.                                                          |
| `allow_new_rooms`       | boolean | If `true`, the bot auto-joins rooms it's invited to; if `false`, it ignores new invites. Re-read on every invite, so it takes effect without a restart.                                            |
| `verify_pinned_link`    | boolean | If `true`, every cycle the bot re-checks on the server that its link is still present and pinned, re-pinning or re-posting if not. Adds one extra request per room per cycle; disabled by default. |

3. Run it:
   ```sh
   python bot.py
   ```

## Required Matrix permissions

Pinning a message means editing the `m.room.pinned_events` **state event**, which
requires a higher power level than simply sending messages:

- **Sending a message** → requires the room's `events_default` power level
  (usually **0**).
- **Pinning** → requires the room's `state_default` power level (usually **50**,
  i.e. moderator).

So a bot left at the default power level can post links but **cannot pin them**.
For pinning to work, the room admin must, in each room:

- give the bot **Moderator** (power level 50), **or**
- lower the level required for *"Manage pinned events"* down to the bot's level,
  under *Room Settings → Roles & Permissions*.

If the bot's power level is below `events_default` it won't even be able to send
messages (you'll see `M_FORBIDDEN … user_level (…) < send_level (…)` in the logs);
raise it to at least 0 to post, and to 50 to also pin.

You don't need to restart the bot after changing its power level: it watches for
power-level changes and pins the current link the moment it's granted the rights,
rather than waiting for the next polling cycle.

## Room history visibility

Give the bot pin rights **and** make the room's history readable if you want people
who join later to see the link right away. The pinned message is one the bot posted
earlier, so a member who joins afterwards can only see it if the room's **history
visibility** lets them read messages from before they joined.

Set it to **Shared** (all members can read history) or **world-readable** (anyone
can), under *Room Settings → Security & Privacy → Who can read history*. With the
more restrictive *Members only (since they joined)* setting, new members won't see
the already-posted link until the domain changes and the bot posts a fresh one.

## License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.
