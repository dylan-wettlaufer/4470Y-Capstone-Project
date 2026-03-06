import os
from dotenv import load_dotenv
import json
from openai import OpenAI

load_dotenv()

def extract_events_llm(biography_text, subject_name):
    """
    Extracts events from the given text using OpenAI LLM
    args:
        biography_text (str): The biography text to extract events from
        subject_name (str): The name of the subject
    returns:
        json: A json of the events mentioned in the text
    """
    
    system_prompt = f"""
        You are extracting structured historical events from a biography of {subject_name}.

        TASK:
        Extract major life events explicitly stated in the text.

        For each event, extract:
        - description (should be short, factual, non-narrative and derived from the text)
        - date (ISO 8601 if possible; year or range allowed; null if missing)
        - place (city, region, country)
        - event_type (birth, death, education, appointment, marriage, relocation, military_service, award, other)

        RULES:
        - Do NOT infer or guess information
        - Extract only clearly stated events
        - Focus on major life events
        - Order events chronologically if possible
        - Return valid JSON only

        IMPORTANT CONSTRAINTS:
        - NEVER invent dates. If only a year is mentioned, return "YYYY".
        - Do NOT use "YYYY-01-01" unless explicitly stated in the text.
        - Each item must represent a single historical event, not a summary.
        - Places must be clean labels: "City, Region, Country" when possible.


        Return JSON in this exact format:
        {{
        "events": [
            {{
                "description": "",
                "date": "",
                "place": "",
                "event_type": ""
            }}
        ]
        }}
        """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": biography_text}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    text_response = response.choices[0].message.content
    
    try:
        return json.loads(text_response)
    except json.JSONDecodeError:
        print("Failed to parse JSON from OpenAI output")
        print(text_response)
        return {"events": []}