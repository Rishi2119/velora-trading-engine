from agent.utils.errors import SafetyViolationError

class RiskControlSystem:
    def __init__(self, config):
        self.config = config.get('safety', {})
        self.allow_system_commands = self.config.get('allow_system_commands', False)
        self.allow_file_deletion = self.config.get('allow_file_deletion', False)
        
        # Blacklisted commands or modules
        self.blacklisted_keywords = ['rm -rf', 'format', 'shutdown', 'os.system', 'subprocess']
        
    def validate_action(self, action_type, payload):
        if action_type == 'system_command' and not self.allow_system_commands:
            raise SafetyViolationError("System commands are disabled by safety policy.")
            
        if action_type == 'delete_file' and not self.allow_file_deletion:
            raise SafetyViolationError("File deletion is disabled by safety policy.")
            
        payload_str = str(payload).lower()
        for kw in self.blacklisted_keywords:
            if kw in payload_str:
                raise SafetyViolationError(f"Action contains blacklisted keyword: {kw}")
                
        return True
