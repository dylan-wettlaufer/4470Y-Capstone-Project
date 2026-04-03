import json
import re

def normalize(text):
    #convert text into comparable tokens
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)    
    words = text.split()
    
    return set(words)


def fix_ttl_urls():
    # loads the knowledge graph connections json file that has all the clickable links
    with open('output/knowledge_graph_connections.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # loads the knowledge graph ttl file
    with open('output/knowledge_graph.ttl', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # initializes fixes counter
    fixes = 0

    # finds all person URIs in the ttl file
    ttl_people = re.findall(r'<https://biographi\.ca/person/([^>]+)>', content)


    for conn in data["connections"]:
        json_name = conn["target_person"]
        url = conn["target_url"]
        
        json_tokens = normalize(json_name)

        for ttl_slug in ttl_people:
            ttl_tokens = set(ttl_slug.split('_'))
            
            overlap = json_tokens.intersection(ttl_tokens)
            
            if len(overlap) >= 2:
                old_uri = f'<https://biographi.ca/person/{ttl_slug}>'
                new_uri = f'<{url}>'
                
                if old_uri in content:
                    content = content.replace(old_uri, new_uri)
                    print(f"Fixed: {json_name} → {ttl_slug}")
                    fixes += 1
                    break

    with open('output/knowledge_graph.ttl', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nDone! Total fixes: {fixes}")


# merges the clickable links into the persons json file
def merge_links_into_json(persons_json, clickable_links):
    existing_names = {p["name"].lower() for p in persons_json["persons"]}

    for link in clickable_links["connections"]:
        name = link["target_person"]

        if name.lower() not in existing_names:
            persons_json["persons"].append({
                "name": name,
                "relation_to_subject": ["other"],
                "roles": [],
                "url": link.get("target_url", "")
            })
        else:
            for p in persons_json["persons"]:
                if p["name"].lower() == name.lower():
                    if "target_url" in link:
                        p["url"] = link["target_url"]

    return persons_json

# loads the connections with urls json file
def load_connections_with_urls(path):
    """Load JSON file containing connections or clickable links."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
