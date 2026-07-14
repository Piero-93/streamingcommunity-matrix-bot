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

STATE_FILE = "state.json"

def load_state():
    """Load the persisted state from disk, or an empty dict if it doesn't exist yet."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state):
    """Persist the given state dict to disk as JSON."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)