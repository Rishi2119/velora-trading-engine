import os

KILL_SWITCH_FILE = "KILL_SWITCH.ON"

def is_kill_switch_active():
    return os.path.exists(KILL_SWITCH_FILE)
