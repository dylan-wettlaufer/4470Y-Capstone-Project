import spacy
from google import genai
import os
from dotenv import load_dotenv
import json

load_dotenv()

def extract_persons(text):
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(text)

    persons = set()  # use a set to avoid duplicates
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            persons.add(ent.text)

    clean_persons = clean_person_names(persons, 2)
        
    return clean_persons

def clean_person_names(persons, min_words):
        # Clean and deduplicate person names
        cleaned = []
        
        for person in persons:
            # Remove possessives
            clean_name = person.replace("'s", "").replace("'", "").strip()
            
            # Filter by word count
            if len(clean_name.split()) >= min_words:
                cleaned.append(clean_name)
        
        # Deduplicate and sort
        return sorted(set(cleaned))


def extract_persons_llm(biography_text, subject_name):
    
    prompt = f"""You are analyzing a biographical text about {subject_name} from the Dictionary of Canadian Biography.

    Extract ALL person names mentioned in the biography below. For each person:
    1. Provide their FULL, properly formatted name (e.g., "John George Diefenbaker" not "Diefenbaker")
    2. Identify their relationship to {subject_name} (e.g., colleague, spouse, opponent, mentor, prime minister they served under)
    3. Note their role/occupation if mentioned (e.g., Prime Minister, diplomat, journalist)

    IMPORTANT RULES:
    - Only extract PEOPLE, not places, organizations, or book titles
    - Clean up any formatting artifacts like brackets, asterisks, or possessives
    - If a person is mentioned multiple times, list them once with all relationships
    - Include historical figures even if only briefly mentioned
    - If first name is not given but context makes it clear who it is, include the full name

    Return your response as valid JSON in this exact format:
    {{
    "persons": [
        {{
        "name": "Full Name Here",
        "relationships": ["relationship1", "relationship2"],
        "roles": ["role1", "role2"],
        "context": "Brief note about how they relate to the subject"
        }}
    ]
    }}

    BIOGRAPHY TEXT:
    {biography_text}

    Return ONLY the JSON, no other text."""

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) # set up client
    
    response = client.models.generate_content( # generate response
        model="gemini-2.5-flash",  
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    if response.text:
        try:
            persons_data = json.loads(response.text)
            return persons_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response: {response.text}")
            return {"persons": []}
    else:
        return {"persons": []}