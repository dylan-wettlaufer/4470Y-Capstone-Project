import spacy
import os
from dotenv import load_dotenv
import json
from openai import OpenAI

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
    
    # The rules we want the LLM to follow for the output
    system_prompt = f"""
    You are extracting structured biographical data about {subject_name}
    from the Dictionary of Canadian Biography.

    TASK:
    Extract ALL PERSONS mentioned in the text.

    For each person, return:
    1. Full standardized name
    2. Their relationship to {subject_name}, using ONLY the allowed relationship types
    3. Any roles or occupations explicitly stated in the text

    ALLOWED RELATIONSHIP TYPES:
    parent, child, spouse, sibling, ancestor, descendant,
    political_associate, colleague, superior, subordinate,
    mentor, opponent, monarch, friend, other

    RULES:
    - Extract PEOPLE ONLY
    - Do NOT extract {subject_name} 
    - Do NOT include places, organizations, or publications
    - Do NOT invent roles or relationships
    - List each person only once
    - Do NOT include explanations or prose
    - If unsure, use "other"

    RETURN FORMAT (valid JSON only):

    {{
    "persons": [
        {{
        "name": "Full Name",
        "relation_to_subject": ["relationship_type"],
        "roles": ["role1", "role2"]
        }}
    ]
    }}
    """

    user_prompt = biography_text # the biograpy text

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o",   
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    text_response = response.choices[0].message.content

    try:
        return json.loads(text_response)  # JSON output same as Gemini
    except json.JSONDecodeError:
        print("Failed to parse JSON from OpenAI output")
        print(text_response)
        return {"persons": []}

