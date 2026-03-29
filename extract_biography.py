import requests
from bs4 import BeautifulSoup
import re


def extract_info(url): 
    """ Extracts biographies and bibliographies from the DCB website with the given url 
        args:
            url (str): The url of the DCB page to extract biographies and bibliographies from
        returns:
            json: A json of the biographies and bibliographies
    """

    response = requests.get(url)
    response.raise_for_status()  # raises an error if request failed

    html = response.text

    soup = BeautifulSoup(html, 'html.parser')

    # Extract id from url
    person_id = url.rstrip('/').split('/')[-1].replace('.html', '') # ensures .html is not included in the id

    
    subject_name = extract_subject_name(soup) # extract subject name

    biography = extract_bio(soup) # extract bio
    bibliography = extract_biblio(soup)

    # structure output as json
    output = { 
        "url": url,
        "person_id": person_id,
        "subject_name": subject_name,
        "biography": biography,
        "bibliography": bibliography
    }

    return output # return json


def extract_bio(soup):
    """ Extracts the biography from the DCB website with the given soup """

    # Extract the bio content
    bio_section = soup.find("section", {"id": "first", "class": "bio"})
    bio_text = ""

    if bio_section: # remove images
        for img_div in bio_section.find_all("div", id="bio-primary-image"):
            img_div.decompose()

        bio_text = bio_section.get_text(separator="\n", strip=True)
        bio_text = clean_text(bio_text)  # Apply cleaning

    else:
        print("Biography section not found.")

    return bio_text # return biography text

def extract_biblio(soup):
    """ Extracts the bibliography from the DCB website with the given soup """

    biblio_section = soup.find("section", {"id": "second", "class": "biblio"}) # find biblio section
    biblio_text = "";

    if biblio_section: # if text exists, clean it
        biblio_text = biblio_section.get_text(separator="\n", strip=True)
        biblio_text = clean_text(biblio_text)

    else:
        print("Bibliography section not found.")

    return biblio_text


def clean_text(text):
    """ Cleans the text by removing special characters and normalizing spaces """

    # Replace non-breaking spaces and other special spaces with regular spaces
    text = text.replace('\xa0', ' ')
    text = text.replace('\u2009', ' ')  # Thin space
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\u202f', ' ')  # Narrow no-break space

    # Remove extra whitespace around newlines
    text = re.sub(r' *\n *', '\n', text)

    # Replace newlines with spaces
    text = text.replace('\n', ' ')

    # Normalize multiple spaces to single space
    text = re.sub(r' +', ' ', text)

    return text.strip()

def extract_subject_name(soup): 
    """ Extracts the subject name from the DCB website with the given soup """

    bio_section = soup.find("section", {"id": "first", "class": "bio"}) # find the section that contains the bio
    
    if bio_section:
        first_para = bio_section.find("p", class_="FirstParagraph") # first paragraph has the name
        if first_para:
            strong_tag = first_para.find("strong") # subject name has a strong text tag
            if strong_tag: 
                return strong_tag.get_text(strip=True)
    
    return None