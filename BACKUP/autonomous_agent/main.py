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
    # Load environment variables (API keys)
    load_dotenv()
    
    # Load settings
    config = load_config()
    
    # Initialize the Agent Loop
    agent = AutonomousLoop(config)
    
    # Inject an initial test goal
    agent.set_goal("Analyze the current directory and write a summary to system_summary.txt")
    
    try:
        # Run 24/7
        agent.start()
    except KeyboardInterrupt:
        logger.info("Emergency kill switch activated. Shutting down gracefully...")
        agent.stop()
        
if __name__ == "__main__":
    main()
