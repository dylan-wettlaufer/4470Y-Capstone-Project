from extract_biography import extract_info
from ner import extract_persons_llm
from create_rdf import build_rdf
from visualize import visualize_rdf
from event_extractor import extract_events_llm
from bibliography import parse_bibliography_llm, convert_llm_to_bibtex
from ner import extract_persons, extract_persons_llm
from fix_ttl_urls import (load_connections_with_urls, fix_ttl_urls)
from connection_links import scan_page_for_links, save_first_hop_connections


"""
Main file used to run the program.
Imports functions from other files to extract biographies and bibliographies, extract relationships with OpenAI LLM, and convert relationships to RDF triples

Pipeline: 
    1. Extract biography and bibliography from the URL and return a json including the subject name, person id, biography, and bibliography
    2. Scan biography page for valid links and save first-hop connections with AI-detected relationships
    3. Extract persons, relationships, and roles from the biography with a LLM and return a json 
    4. Build rdf triples using the subject, relationship, and object from the LLM and create a ttl file
    5. Fix TTL URLs using connection data and visualize rdf graph

"""


url = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"

json_data = extract_info(url)
print(json_data)
print()

print("Scanning for biography links...")
result = scan_page_for_links(url)
if 'error found: ' in result:
    print(f"Error: {result['error found: ']}")
else:
    print(f"Found {result['total_found']} links ({len(result['valid_links'])} valid)")
    connections = save_first_hop_connections(url, result['valid_links'])
    print(f"Saved {connections['total_connections']} connections")

persons_llm = extract_persons_llm(json_data["biography"], json_data["subject_name"])
print(persons_llm)

print()

events_llm = extract_events_llm(json_data["biography"], json_data["subject_name"])
print(events_llm)

person_id = build_rdf(persons_llm, json_data["subject_name"], json_data["person_id"], url, events_llm)

print()
print("Fixing TTL URLs...")
print("person_id: " + person_id)
fix_ttl_urls(json_data["person_id"])
visualize_rdf("output/" + person_id + "_" + "knowledge_graph.ttl")


print()
llm_result = parse_bibliography_llm(json_data["bibliography"])
convert_llm_to_bibtex(llm_result, "output/llm_bibliography.bib")
