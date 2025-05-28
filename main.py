import os
from agents.classifier_agent import ClassifierAgent
from memory.shared_memory import shared_memory_instance, MEMORY_FILE
import json

def load_sample_data(filepath):
    try:
        if filepath.lower().endswith(".json"):
            with open(filepath, 'r') as f:
                return json.load(f)
        else:
            if filepath.lower().endswith(".pdf"):
                return filepath
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Error loading sample data from {filepath}: {e}")
        return None

if __name__ == "__main__":
    print("Starting Multi-Agent AI System...")
    classifier = ClassifierAgent()
    print("\n--- Processing Email RFQ (Text File) ---")
    email_rfq_path = "sample_inputs/email_rfq.txt"
    email_rfq_content = load_sample_data(email_rfq_path)
    if email_rfq_content:
        thread_id_rfq, result_rfq = classifier.process(
            input_data=email_rfq_content,
            source_identifier=os.path.basename(email_rfq_path),
            source_type="file_upload_text_email"
        )
        print(f"RFQ Processing Result (Thread: {thread_id_rfq}):")
    print("\n--- Processing JSON Invoice (File) ---")
    json_invoice_path = "sample_inputs/invoice_data.json"
    if os.path.exists(json_invoice_path):
        thread_id_invoice, result_invoice = classifier.process(
            input_data=json_invoice_path,
            source_identifier=os.path.basename(json_invoice_path),
            source_type="file_upload_json"
        )
        print(f"Invoice Processing Result (Thread: {thread_id_invoice}):")
    print("\n--- Processing Email Complaint (Text File) ---")
    email_complaint_path = "sample_inputs/email_complaint.txt"
    email_complaint_content = load_sample_data(email_complaint_path)
    if email_complaint_content:
        thread_id_complaint, result_complaint = classifier.process(
            input_data=email_complaint_content,
            source_identifier=os.path.basename(email_complaint_path),
            source_type="file_upload_text_email",
        )
        print(f"Complaint Processing Result (Thread: {thread_id_complaint}):")
    print("\n--- Processing Regulation Document (Text File) ---")
    regulation_path = "sample_inputs/some_regulation.txt"
    regulation_content = load_sample_data(regulation_path)
    if regulation_content:
        thread_id_reg, result_reg = classifier.process(
            input_data=regulation_content,
            source_identifier=os.path.basename(regulation_path),
            source_type="file_upload_text_document"
        )
        print(f"Regulation Processing Result (Thread: {thread_id_reg}):")
    print("\n--- Processing PDF Document (Simulated) ---")
    pdf_path = "sample_inputs/document.pdf"
    if os.path.exists(pdf_path):
        thread_id_pdf, result_pdf = classifier.process(
            input_data=pdf_path,
            source_identifier=os.path.basename(pdf_path),
            source_type="file_upload_pdf"
        )
        print(f"PDF Processing Result (Thread: {thread_id_pdf}):")
    shared_memory_instance.print_log()
    print("\nMulti-Agent AI System run complete.")
    print(f"Memory log saved to: {MEMORY_FILE}")