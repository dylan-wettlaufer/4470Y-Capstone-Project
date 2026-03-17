from extract_biography import extract_info
from ner import extract_persons, extract_persons_llm
from create_rdf import build_rdf
from visualize import visualize_rdf
from event_extractor import extract_events_llm
from bibliography import parse_bibliography_llm, convert_llm_to_bibtex


"""
Main file used to run the program.
Imports functions from other files to extract biographies and bibliographies, extract relationships with OpenAI LLM, and convert relationships to RDF triples

Pipeline: 
    1. Extract biography and bibliography from the URL and return a json including the subject name, person id, biography, and bibliography
    2. Extract persons, relationshsips, and roles from the biography with a LLM and return a json 
    3. Build rdf triples using the subject, relationship, and object from the LLM and create a ttl file
    4. Visulize rdf graph

"""


url = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"

json_data = extract_info(url)
print(json_data)

print()

persons_llm = extract_persons_llm(json_data["biography"], json_data["subject_name"])
print(persons_llm)

print()

events_llm = extract_events_llm(json_data["biography"], json_data["subject_name"])
print(events_llm)

print()

build_rdf(persons_llm, json_data["subject_name"], json_data["person_id"], url, events_llm)
visualize_rdf("output/knowledge_graph.ttl")

print()
llm_result = parse_bibliography_llm(json_data["bibliography"])
convert_llm_to_bibtex(llm_result, "output/llm_bibliography.bib")
