# agents/email_agent.py
from .base_agent import BaseAgent
from utils.llm_utils import call_gemini
import re

class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__("EmailAgent")

    def _extract_basic_sender(self, email_content: str) -> str:
        """Basic regex to find 'From:' line. LLM can be more robust."""
        match = re.search(r"From:\s*([^\n]+)", email_content, re.IGNORECASE)
        return match.group(1).strip() if match else "Unknown"

    def process(self, email_content: str, source_identifier: str, thread_id: str, initial_intent: str = "Unknown"):
        """Processes email content."""
        print(f"EmailAgent processing: {source_identifier} (Intent: {initial_intent})")

        # 1. Extract Sender (can be basic regex or LLM for robustness)
        sender = self._extract_basic_sender(email_content)
        if sender == "Unknown": # Fallback to LLM if regex fails
            sender_prompt = f"Extract the sender's full email address or name from the following email content. If multiple are present, pick the primary sender. If none, respond with 'Unknown'.\n\nEmail Content:\n{email_content[:1000]}\n\nSender:"
            sender = call_gemini(sender_prompt, temperature=0.1)

        # 2. Refine Intent (optional, classifier might be enough)
        # For this example, we'll use the initial_intent from the classifier.
        # If needed, you could ask LLM to refine:
        # refine_intent_prompt = f"The email was initially classified as '{initial_intent}'. Based on the full content, refine this intent or confirm it. Content: {email_content[:1500]}"
        # refined_intent = call_gemini(refine_intent_prompt)
        refined_intent = initial_intent # Using classifier's intent

        # 3. Assess Urgency
        urgency_prompt = f"Assess the urgency of the following email content as Low, Medium, or High. Provide only the urgency level.\n\nEmail Content:\n{email_content[:1500]}\n\nUrgency:"
        urgency = call_gemini(urgency_prompt, temperature=0.2)
        if urgency.lower() not in ["low", "medium", "high"]:
            urgency = "Medium" # Default if LLM gives weird output

        # 4. Format for CRM-style usage (Summary, Key Points)
        crm_summary_prompt = f"""
        Analyze the following email content, which has been identified as related to '{refined_intent}'.
        Provide a concise summary suitable for a CRM system.
        Include:
        - Main topic/request.
        - Key entities mentioned (people, companies, products if applicable).
        - Any explicit action items or deadlines.

        Email Content:
        ---
        {email_content[:2000]}
        ---
        CRM Summary:
        """
        crm_summary = call_gemini(crm_summary_prompt, temperature=0.5)

        extracted_info = {
            "sender": sender,
            "intent": refined_intent,
            "urgency": urgency.capitalize(),
            "crm_summary": crm_summary,
            "original_content_preview": email_content[:200] + "..."
        }

        self._log_to_memory(
            source_identifier=source_identifier,
            source_type="email_content",
            classified_format="Email", # Assuming it's an email
            classified_intent=refined_intent,
            extracted_data=extracted_info,
            thread_id=thread_id,
            notes="Processed by EmailAgent."
        )
        return extracted_info