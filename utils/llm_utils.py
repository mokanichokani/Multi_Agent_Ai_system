# utils/llm_utils.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in .env file.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

def call_gemini(prompt: str, temperature=0.3) -> str:
    """
    Sends a prompt to Gemini and returns the text response.
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature
            )
        )
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text.strip()
        else:
            print("Warning: Gemini response was empty or malformed.")
            return "Error: No content in response"
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return f"Error: {str(e)}"

if __name__ == '__main__':
    test_prompt = "What is the capital of France?"
    answer = call_gemini(test_prompt)
    print(f"Prompt: {test_prompt}")
    print(f"Gemini: {answer}")