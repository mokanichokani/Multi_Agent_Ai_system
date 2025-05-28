# memory/shared_memory.py
import json
import datetime
import uuid
import os

MEMORY_FILE = "shared_memory_log.json"

class SharedMemory:
    def __init__(self):
        self.log = []
        self.load_from_file()

    def add_entry(self, source_identifier: str, source_type: str, classified_format: str = None,
                  classified_intent: str = None, agent_processed: str = None,
                  extracted_data: dict = None, thread_id: str = None, notes: str = None):
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        entry = {
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "thread_id": thread_id,
            "source_identifier": source_identifier,
            "source_type": source_type,
            "classified_format": classified_format,
            "classified_intent": classified_intent,
            "agent_processed": agent_processed,
            "extracted_data": extracted_data if extracted_data else {},
            "notes": notes
        }
        self.log.append(entry)
        self.save_to_file()
        print(f"Memory Added: {entry['log_id']} for thread {thread_id}")
        return thread_id

    def get_last_entry_by_thread(self, thread_id: str):
        thread_entries = [entry for entry in self.log if entry["thread_id"] == thread_id]
        return thread_entries[-1] if thread_entries else None

    def get_full_thread_history(self, thread_id: str):
        return [entry for entry in self.log if entry["thread_id"] == thread_id]

    def save_to_file(self):
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.log, f, indent=4)

    def load_from_file(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r') as f:
                    self.log = json.load(f)
                print(f"Loaded {len(self.log)} entries from {MEMORY_FILE}")
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {MEMORY_FILE}. Starting with empty memory.")
                self.log = []
        else:
            print(f"{MEMORY_FILE} not found. Starting with empty memory.")
            self.log = []

    def print_log(self):
        print("\n--- Shared Memory Log ---")
        for entry in self.log:
            print(json.dumps(entry, indent=2))
        print("-------------------------\n")

shared_memory_instance = SharedMemory()