# agents/classifier_agent.py
import os
from .base_agent import BaseAgent
from .json_agent import JSONAgent
from .email_agent import EmailAgent
from utils.llm_utils import call_gemini
import json
import io # For handling byte streams from Streamlit
try:
    from PyPDF2 import PdfReader # For PDF text extraction
except ImportError:
    print("PyPDF2 not installed. PDF processing will be limited to filename detection.")
    PdfReader = None


# Initialize child agents here or pass them during instantiation
json_agent_instance = JSONAgent()
email_agent_instance = EmailAgent()


class ClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("ClassifierAgent")
        self.json_agent = json_agent_instance
        self.email_agent = email_agent_instance

    def _extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extracts text from PDF bytes."""
        if not PdfReader:
            return "PDF text extraction skipped (PyPDF2 not available)."
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip() if text else "No text found in PDF."
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return f"Error extracting PDF text: {e}"

    def _classify_format(self, data: any, filename: str = None, is_uploaded_file: bool = False) -> str:
        """Classifies the format of the input data.
        `is_uploaded_file` indicates if 'data' is a file object from an uploader.
        """
        if isinstance(data, dict):
            return "JSON"
        if isinstance(data, str): # Could be raw text, or path to file
            try:
                json.loads(data)
                return "JSON"
            except json.JSONDecodeError:
                if filename and filename.lower().endswith(".pdf"):
                    return "PDF"
                if "@" in data and ("Subject:" in data or "From:" in data or "To:" in data):
                    return "Email"
                return "Text/Email"
        # Handling uploaded files (like from Streamlit)
        if hasattr(data, 'name') and hasattr(data, 'getvalue'): # Likely an uploaded file object
            if data.name.lower().endswith(".pdf"):
                return "PDF"
            if data.name.lower().endswith(".json"):
                return "JSON"
            if data.name.lower().endswith((".txt", ".eml")):
                return "Text/Email" # Or just "Text" and let intent figure it out
        # Fallback if it's a path (as in original main.py)
        if filename and filename.lower().endswith(".pdf"):
            return "PDF"
        return "Unknown"

    def _classify_intent(self, text_content: str, source_format: str) -> str:
        # ... (no changes to this method needed for now)
        intents = ["Invoice", "RFQ", "Complaint", "Regulation", "General Inquiry", "Order Confirmation", "Other"]
        prompt = f"""
        Given the following {source_format} content, classify its primary intent.
        Choose one of the following intents: {', '.join(intents)}.
        If none seem to fit well, choose 'General Inquiry'.

        Content:
        ---
        {text_content[:2000]}
        ---
        Primary Intent:
        """
        classified_intent = call_gemini(prompt, temperature=0.2)
        valid_intents_lower = [i.lower() for i in intents]
        if classified_intent.lower() in valid_intents_lower:
            return intents[valid_intents_lower.index(classified_intent.lower())]
        print(f"Warning: LLM returned an unexpected intent '{classified_intent}'. Defaulting to 'Other'.")
        return "Other"


    def process(self, input_data: any, source_identifier: str, source_type: str = "unknown_source", thread_id: str = None):
        print(f"\nClassifierAgent processing: {source_identifier}")

        content_for_intent_classification = ""
        # `input_data` can now also be a Streamlit UploadedFile object
        is_uploaded_file_object = hasattr(input_data, 'name') and hasattr(input_data, 'getvalue')

        if is_uploaded_file_object:
            filename_for_format_classification = input_data.name
            # Determine format based on uploaded file's name first
            classified_format = self._classify_format(input_data, filename=input_data.name, is_uploaded_file=True)

            if classified_format == "PDF":
                pdf_bytes = input_data.getvalue()
                content_for_intent_classification = self._extract_text_from_pdf_bytes(pdf_bytes)
                if not content_for_intent_classification.startswith("Error extracting PDF text") and \
                   content_for_intent_classification != "No text found in PDF." and \
                   content_for_intent_classification != "PDF text extraction skipped (PyPDF2 not available).":
                    print(f"Extracted text from PDF '{source_identifier}': {len(content_for_intent_classification)} chars")
                else:
                    print(f"Warning/Error with PDF '{source_identifier}': {content_for_intent_classification}")
            elif classified_format == "JSON":
                try:
                    json_content_bytes = input_data.getvalue()
                    loaded_json = json.loads(json_content_bytes.decode('utf-8'))
                    content_for_intent_classification = json.dumps(loaded_json, indent=2)
                    input_data = loaded_json # Replace file obj with parsed dict for JSON agent
                except Exception as e:
                    content_for_intent_classification = f"Error reading/parsing uploaded JSON: {e}"
                    print(f"Error processing uploaded JSON {source_identifier}: {e}")
                    # We might want to handle this error more gracefully, e.g., by logging and returning
            else: # Text/Email from uploaded file
                try:
                    text_bytes = input_data.getvalue()
                    content_for_intent_classification = text_bytes.decode('utf-8')
                except Exception as e:
                    content_for_intent_classification = f"Error reading uploaded text file: {e}"
                    print(f"Error processing uploaded text file {source_identifier}: {e}")
        else: # Handling for string data or file paths (original logic)
            filename_for_format_classification = None
            if isinstance(input_data, str) and source_identifier.lower().endswith((".txt", ".eml")):
                content_for_intent_classification = input_data
                filename_for_format_classification = source_identifier
            elif isinstance(input_data, dict):
                content_for_intent_classification = json.dumps(input_data, indent=2)
            elif isinstance(input_data, str) and os.path.exists(input_data): # File path
                filename_for_format_classification = input_data
                if input_data.lower().endswith(".pdf"):
                    # This path might be less used with Streamlit, but keep for compatibility
                    if PdfReader:
                        try:
                            with open(input_data, 'rb') as f_pdf:
                                content_for_intent_classification = self._extract_text_from_pdf_bytes(f_pdf.read())
                        except Exception as e:
                            content_for_intent_classification = f"Error reading PDF file {input_data}: {e}"
                    else:
                        content_for_intent_classification = f"Content of PDF file: {input_data} (PyPDF2 not available)"
                    print(f"NOTE: PDF content extraction from path: {input_data}")
                elif input_data.lower().endswith(".json"):
                    with open(input_data, 'r') as f:
                        loaded_json = json.load(f)
                        content_for_intent_classification = json.dumps(loaded_json, indent=2)
                        input_data = loaded_json
                else:
                    with open(input_data, 'r') as f:
                        content_for_intent_classification = f.read()
            else: # Raw string input
                content_for_intent_classification = str(input_data)
            classified_format = self._classify_format(input_data, filename_for_format_classification)


        # If format still unknown from file object, try content (less reliable for binary)
        if classified_format == "Unknown" and not is_uploaded_file_object:
             classified_format = self._classify_format(content_for_intent_classification, filename_for_format_classification)


        classified_intent = self._classify_intent(content_for_intent_classification, classified_format)

        current_thread_id = self._log_to_memory(
            source_identifier=source_identifier,
            source_type=source_type,
            classified_format=classified_format,
            classified_intent=classified_intent,
            thread_id=thread_id,
            notes="Initial classification"
        )
        print(f"Classifier: Format={classified_format}, Intent={classified_intent}, ThreadID={current_thread_id}")

        if classified_format == "JSON":
            # input_data should be a dict here. If it came from an uploaded file, it was converted.
            if not isinstance(input_data, dict):
                try: # Last attempt to parse if it's a string
                    input_data_parsed = json.loads(content_for_intent_classification) # Use content_for_intent
                except json.JSONDecodeError:
                    print(f"Error: Could not parse as JSON for {source_identifier} before routing.")
                    self._log_to_memory(source_identifier, source_type, classified_format, classified_intent,
                                        extracted_data={"error": "Failed to parse JSON string/content"},
                                        thread_id=current_thread_id, notes="JSON parsing error before routing")
                    return current_thread_id, {"error": "Failed to parse JSON content"}
                return current_thread_id, self.json_agent.process(input_data_parsed, source_identifier=source_identifier, thread_id=current_thread_id, initial_intent=classified_intent)
            return current_thread_id, self.json_agent.process(input_data, source_identifier=source_identifier, thread_id=current_thread_id, initial_intent=classified_intent)
        elif classified_format in ["Email", "Text/Email"]:
            return current_thread_id, self.email_agent.process(content_for_intent_classification, source_identifier=source_identifier, thread_id=current_thread_id, initial_intent=classified_intent)
        elif classified_format == "PDF":
            # For PDF, EmailAgent might be suitable if text is extracted
            # Or you could have a dedicated PDF summary agent
            # We will pass the extracted text to EmailAgent as a generic text processor for now
            print(f"PDF detected for {source_identifier}. Routing extracted text to EmailAgent for general processing.")
            # Note: If content_for_intent_classification is an error message, EmailAgent will process that.
            return current_thread_id, self.email_agent.process(content_for_intent_classification, source_identifier=source_identifier, thread_id=current_thread_id, initial_intent=classified_intent)
        else:
            print(f"Unknown format for {source_identifier}. No specific agent to route to. Content preview: {content_for_intent_classification[:100]}")
            extracted_data = {"status": f"Unknown format: {classified_format}"}
            self._log_to_memory(
                source_identifier=source_identifier,
                source_type=source_type,
                classified_format=classified_format,
                classified_intent=classified_intent,
                extracted_data=extracted_data,
                thread_id=current_thread_id,
                notes="Unknown format, not routed."
            )
            return current_thread_id, extracted_data    