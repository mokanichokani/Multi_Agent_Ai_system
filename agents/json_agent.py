# agents/json_agent.py
from .base_agent import BaseAgent
from utils.llm_utils import call_gemini

class JSONAgent(BaseAgent):
    def __init__(self):
        super().__init__("JSONAgent")
        self.target_schemas = {
            "Invoice": {
                "required_fields": ["invoice_id", "customer_name", "total_amount", "items"],
                "optional_fields": ["due_date", "invoice_date"],
                "item_schema": {"name": str, "quantity": int, "unit_price": float}
            },
            "RFQ": {
                "required_fields": ["rfq_id", "product_description", "quantity_needed"],
                "optional_fields": ["deadline", "contact_person"]
            }
        }

    def _validate_and_reformat(self, data: dict, intent: str) -> (dict, list):
        schema = self.target_schemas.get(intent)
        if not schema:
            return data, [f"No specific schema defined for intent '{intent}'. Passing through data."]
        reformatted_data = {}
        anomalies = []
        for field in schema["required_fields"]:
            if field in data:
                reformatted_data[field] = data[field]
            else:
                anomalies.append(f"Missing required field: {field}")
        for field in schema.get("optional_fields", []):
            if field in data:
                reformatted_data[field] = data[field]
        if intent == "Invoice" and "items" in reformatted_data:
            if not isinstance(reformatted_data["items"], list):
                anomalies.append("Field 'items' should be a list.")
            else:
                for i, item in enumerate(reformatted_data["items"]):
                    if not isinstance(item, dict):
                        anomalies.append(f"Item at index {i} is not a dictionary.")
                        continue
                    for key, item_type in schema["item_schema"].items():
                        if key not in item:
                            anomalies.append(f"Item at index {i} missing field: {key}")
                        elif not isinstance(item[key], item_type):
                            anomalies.append(f"Item at index {i}, field '{key}': Expected type {item_type.__name__}, got {type(item[key]).__name__}")
        for key in data:
            if key not in reformatted_data:
                reformatted_data[key] = data[key]
                anomalies.append(f"Unexpected field found: {key} (included as-is)")
        if not anomalies and not reformatted_data:
             anomalies.append("Input JSON does not match any fields in the target schema.")
        return reformatted_data, anomalies

    def process(self, data: dict, source_identifier: str, thread_id: str, initial_intent: str = "Unknown"):
        print(f"JSONAgent processing: {source_identifier} for intent: {initial_intent}")
        reformatted_data, anomalies = self._validate_and_reformat(data, initial_intent)
        if anomalies:
            print(f"Anomalies found in JSON for {source_identifier}: {anomalies}")
            reformatted_data["_anomalies"] = anomalies
        extracted_info = {
            "original_data_preview": {k: str(v)[:100] + '...' if len(str(v)) > 100 else v for k, v in data.items()},
            "reformatted_data": reformatted_data,
            "schema_applied": initial_intent,
            "anomalies_detected": anomalies if anomalies else "None"
        }
        self._log_to_memory(
            source_identifier=source_identifier,
            source_type="json_payload",
            classified_format="JSON",
            classified_intent=initial_intent,
            extracted_data=extracted_info,
            thread_id=thread_id,
            notes="Processed by JSONAgent."
        )
        return extracted_info