from extract_biography import extract_info
from ner import extract_persons


url = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"

json_data = extract_info(url)
print(json_data)

print()

persons = extract_persons(json_data["biography"])
for p in persons:
    print(p)

'''
response = requests.get(url)
response.raise_for_status()  # raises an error if request failed

html = response.text

soup = BeautifulSoup(html, 'html.parser')

# Extract the bio content
bio_section = soup.find("section", {"id": "first", "class": "bio"})

if bio_section:
    for img_div in bio_section.find_all("div", id="bio-primary-image"):
        img_div.decompose()

    bio_text = bio_section.get_text(separator="\n", strip=True)
else:
    print("Biography section not found.")

# Extract the bibliography content
biblio_section = soup.find("section", {"id": "second", "class": "biblio"})

if biblio_section:
    biblio_text = biblio_section.get_text(separator="\n", strip=True)
else:
    print("Bibliography section not found.")

print(bio_text);

nlp = spacy.load("en_core_web_sm")

doc = nlp(bio_text)

# Extract PERSON entities
persons = set()  # use a set to avoid duplicates
for ent in doc.ents:
    if ent.label_ == "PERSON":
        persons.add(ent.text)

# --- Cleaning steps ---
# Remove single-word names (likely not full people)
clean_persons = [p for p in persons if len(p.split()) > 1]

# Remove possessives / trailing apostrophes
clean_persons = [p.replace("’s", "").replace("'", "").strip() for p in clean_persons]

# Deduplicate and sort
clean_persons = sorted(set(clean_persons))

# Print cleaned list
print("Cleaned Persons found:")
for p in clean_persons:
    print(p)
    
'''