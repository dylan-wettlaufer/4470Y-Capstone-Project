import requests
from bs4 import BeautifulSoup
import re

def extract_info(url): 
    response = requests.get(url)
    response.raise_for_status()  # raises an error if request failed

    html = response.text

    soup = BeautifulSoup(html, 'html.parser')

    # Extract id from url
    person_id = url.rstrip('/').split('/')[-1]
    
    biography = extract_bio(soup)
    bibliography = extract_biblio(soup)

    output = {
        "url": url,
        "person_id": person_id,
        "biography": biography,
        "bibliography": bibliography
    }

    return output


def extract_bio(soup):
    bio_section = soup.find("section", {"id": "first", "class": "bio"})

    # Extract the bio content
    bio_section = soup.find("section", {"id": "first", "class": "bio"})
    bio_text = ""

    if bio_section:
        for img_div in bio_section.find_all("div", id="bio-primary-image"):
            img_div.decompose()

        bio_text = bio_section.get_text(separator="\n", strip=True)
        bio_text = clean_text(bio_text)  # Apply cleaning

    else:
        print("Biography section not found.")

    return bio_text

def extract_biblio(soup):
    biblio_section = soup.find("section", {"id": "second", "class": "biblio"})
    biblio_text = "";

    if biblio_section:
        biblio_text = biblio_section.get_text(separator="\n", strip=True)
        biblio_text = clean_text(biblio_text)

    else:
        print("Bibliography section not found.")

    return biblio_text
    

def clean_text(text):
    """Remove special whitespace characters and normalize text."""
    # Replace non-breaking spaces and other special spaces with regular spaces
    text = text.replace('\xa0', ' ')
    text = text.replace('\u2009', ' ')  # Thin space
    text = text.replace('\u200b', '')   # Zero-width space
    text = text.replace('\u202f', ' ')  # Narrow no-break space
    
    # Normalize multiple spaces to single space
    text = re.sub(r' +', ' ', text)
    
    # Remove extra whitespace around newlines
    text = re.sub(r' *\n *', '\n', text)

    # Replace newlines with spaces
    text = text.replace('\n', ' ')
    
    return text.strip()