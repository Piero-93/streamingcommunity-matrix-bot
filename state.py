import json

STATE_FILE = "state.json"

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)