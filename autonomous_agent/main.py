import yaml
import os
import sys
from dotenv import load_dotenv

# Ensure 'agent' package is discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.core.loop import AutonomousLoop
from agent.utils.logger import logger

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    # Load environment variables (.env file in this directory)
    load_dotenv()

    # Load config.yaml
    config = load_config()

    # Initialize the Agent Loop
    # The loop automatically injects the default trading goal on startup.
    # To override: agent.set_goal("Your custom goal here")
    agent = AutonomousLoop(config)

    # Run 24/7 (Ctrl+C to stop cleanly)
    agent.start()

if __name__ == "__main__":
    main()
