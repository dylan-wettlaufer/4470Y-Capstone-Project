import requests
from bs4 import BeautifulSoup
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Function to scan a biography page for valid biography links
def scan_page_for_links(page_url):
    """
    scans a biography page for valid biography links.
    args:
        page_url: URL of the biography page to scan
    returns:
        dictionary with valid_links, invalid_links, and total_found
    """
    try:
        # get the page and its content
        response = requests.get(page_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # initialize lists for valid and invalid links
        valid_links = []
        invalid_links = []
        
        # process all links on the page
        for link in soup.find_all('a', href=True):
            href_link = link.get('href')
            text = link.get_text(strip=True)
            title = link.get('title', '')
            
            # skip empty or very short text
            if len(text) < 2:
                continue
                
            # check if link is invalid (javascript:void(0) means invalid)
            if href_link == "javascript:void(0)" or "javascript:void(0)" in href_link:
                invalid_links.append({
                    'name': text,
                    'href': href_link,
                    'title': title,
                    'status': 'INVALID javascript:void(0) link'
                })
            else:
                # check if link is a valid biography link and appends to valid_links or invalid_links
                if href_link.startswith('/en/bio/') or href_link.startswith('https://www.biographi.ca/en/bio/'):
                    valid_links.append({
                        'name': text,
                        'href': href_link,
                        'title': title,
                        'status': 'VALID'
                    })
                else:
                    invalid_links.append({
                        'name': text,
                        'href': href_link,
                        'title': title,
                        'status': 'INVALID link'
                    })
        
        # return results
        return {
            'valid_links': valid_links,
            'invalid_links': invalid_links,
            'total_found': len(valid_links) + len(invalid_links)
        }
        
    except Exception as e:
        return {'error found: ': str(e)}

# function used to check and determine relationships between source person and target people using GPT-4o
def detect_all_relationships_with_llm(source_person, target_people, biography_text):
    """
    uses GPT-4o to determine relationships between source person and target people.
    args:
        source_person: Name of the source person (biography subject)
        target_people: List of target person names to analyze relationships with
        biography_text: Full biography text for context
    returns:
        dictionary mapping each person to their relationship type
    """
    # initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # system prompt for the AI to extract relationships. This prompt had to be changed a couple times
    # to get the best results or more accurate results.
    system_prompt = f"""
You are an expert at extracting relationships from biographies.

TASK:
Determine the relationship between {source_person} (the subject) and EACH person listed below.

ALLOWED RELATIONSHIP TYPES (choose only one):
friend, family, political_opponent, colleague, mentor_mentee, political, mentioned

RULES:
- Return JSON ONLY
- Format MUST be a dictionary where each key is a person's name and value is their relationship:

{{
  "PERSON_NAME_1": "relationship_type",
  "PERSON_NAME_2": "relationship_type",
  ...
}}

- Be aggressive in identifying relationships!
- "political": if they worked in government, politics, or policy together
- "political_opponent": if they disagreed, competed, or were from opposing parties
- "colleague": if they worked together in any professional capacity
- "family": if they're related by blood or marriage
- "friend": if there's evidence of friendship
- "mentor_mentee": if one mentored or guided the other
- "mentioned": only if they're just passingly named with no context

HISTORICAL CONTEXT: These are Canadian political figures, so most relationships will be "political" or "colleague".
"""

    # format the list of people for the prompt
    people_list = "\n".join([f"- {person}" for person in target_people])
    
    # user prompt with biography text
    user_prompt = f"""
Based on this biography of {source_person}, determine the relationship with each person:

{people_list}

BIOGRAPHY TEXT:
{biography_text}

Return the relationships as a JSON dictionary.
"""

    # make API call to OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    # get the response text
    text_response = response.choices[0].message.content

    # parse JSON response
    try:
        return json.loads(text_response)
    except json.JSONDecodeError:
        print("Failed to parse JSON from OpenAI output")
        print(text_response)
        # return default relationships if parsing fails
        return {person: "mentioned" for person in target_people}

# function to extract biography text and save first-hop connections with AI-detected relationships
def save_first_hop_connections(page_url, valid_links, output_file="output/knowledge_graph_connections.json"):
    """
    extracts biography text and saves first-hop connections with AI-detected relationships.
    args:
        page_url: URL of the source biography page
        valid_links: List of valid biography links from scan_page_for_links
        output_file: Path where to save the connections JSON   
    returns:
        dictionary containing the connections data structure
    """
    # extract person name from URL
    person_name = page_url.split('/')[-1].replace('.html', '').replace('_', ' ').title()
    
    # get the full biography text for AI analysis
    try:
        response = requests.get(page_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # try to find main content area
        main_content = soup.find('div', class_='bio-content') or soup.find('main') or soup.find('article')
        if main_content:
            biography_text = main_content.get_text()
        else:
            # fallback: remove navigation and get all text
            for nav in soup.find_all(['nav', 'header', 'footer']):
                nav.decompose()
            biography_text = soup.get_text()
    except:
        biography_text = ""
    
    # create connections data structure
    connections = {
        "source_person": person_name,
        "source_url": page_url,
        "connections": [],
        "total_connections": len(valid_links),
        "extraction_date": "2026-03-23",
        "relationship_detection": "ai_enhanced"
    }
    
    # get all target names for batch processing
    all_target_names = [link['name'] for link in valid_links]
    print(f"Getting relationships for all {len(all_target_names)} people in one API call...")
    
    # get all relationships in one API call
    all_relationships = detect_all_relationships_with_llm(person_name, all_target_names, biography_text)
    
    # process each valid link and create connection
    for link in valid_links:
        # get relationship from the batch result
        relationship_type = all_relationships.get(link['name'], 'mentioned')
        
        # create connection object
        connection = {
            "target_person": link['name'],
            "target_url": f"https://www.biographi.ca{link['href']}",
            "relationship_type": relationship_type,
            "connection_strength": "first_hop"
        }
        connections["connections"].append(connection)
        
        # show progress
        print(f"  Searched for {link['name']} - Relationship: {relationship_type}")
    
    # save to JSON file
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(connections, f, indent=2, ensure_ascii=False)
    
    # print summary
    print(f"\n Saved {len(valid_links)} first-hop connections to {output_file}")
    print(f" Source: {person_name}")
    return connections

# if __name__ == "__main__":
#     # calls the scan_page_for_links function and prints the results including all valid clickable links
#     page_url = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"
    
#     result = scan_page_for_links(page_url)
    
#     if 'error found: ' in result:
#         print(f"Error: {result['error found: ']}")
#     else:
#         print(f"Found {result['total_found']} links ({len(result['valid_links'])} valid)")
        
#         for link in result['valid_links']:
#             print(f"  {link['name']}")
        
#         connections = save_first_hop_connections(page_url, result['valid_links'])
        
#         print(f"Saved {connections['total_connections']} connections to knowledge_graph_connections.json")