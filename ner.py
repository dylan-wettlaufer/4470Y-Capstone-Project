import spacy

def extract_persons(text):
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(text)

    # Extract PERSON entities
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