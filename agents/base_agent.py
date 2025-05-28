# agents/base_agent.py
from memory.shared_memory import shared_memory_instance

class BaseAgent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.memory = shared_memory_instance # All agents use the same memory instance

    def process(self, data, thread_id: str = None, **kwargs):
        raise NotImplementedError("Each agent must implement the 'process' method.")

    def _log_to_memory(self, source_identifier: str, source_type: str,
                       classified_format: str = None, classified_intent: str = None,
                       extracted_data: dict = None, thread_id: str = None, notes: str = None):
        """Helper to log processing results to shared memory."""
        return self.memory.add_entry(
            source_identifier=source_identifier,
            source_type=source_type,
            classified_format=classified_format,
            classified_intent=classified_intent,
            agent_processed=self.agent_name,
            extracted_data=extracted_data,
            thread_id=thread_id,
            notes=notes
        )