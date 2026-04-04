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
    pattern = r'<https://biographi\.ca/person/([^>]+)>'

    ttl_people = re.findall(pattern, content)


    for conn in data["connections"]:
        json_name = conn["target_person"]
        url = conn["target_url"]
        
        json_tokens = normalize(json_name)

        for ttl_slug in ttl_people:
            ttl_tokens = set(ttl_slug.split('_'))
            
            overlap = json_tokens.intersection(ttl_tokens)
            # if at least 2 tokens match then we know we need to fix the url
            if len(overlap) >= 2:
                old_uri = f'<https://biographi.ca/person/{ttl_slug}>'
                new_uri = f'<{url}>'
                
                if old_uri in content:
                    content = content.replace(old_uri, new_uri)
                    print(f"Fixed: {json_name} to {ttl_slug}")
                    fixes += 1
                    break

    with open('output/knowledge_graph.ttl', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nDone! Total fixes: {fixes}")

# loads the connections with urls json file
def load_connections_with_urls(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)