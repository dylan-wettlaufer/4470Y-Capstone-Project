from extract_biography import extract_info
from ner import extract_persons, extract_persons_llm
from create_rdf import build_rdf
from visualize import visualize_rdf
"""
Main file used to run the program.
Imports functions from other files to extract biographies and bibliographies, extract relationships with OpenAI LLM, and convert relationships to RDF triples

Pipeline: 
    1. Extract biography and bibliography from the URL and return a json including the subject name, person is, biography, and bibliography
    2. Extract persons, relationshsips, and roles from the biography with a LLM and return a json 
    3. Build rdf triples using the subject, relationship, and object from the LLM and create a ttl file
    4. Visulize rdf graph

"""


url = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"

json_data = extract_info(url)
print(json_data)

print()

"""
persons = extract_persons(json_data["biography"])

for p in persons:
    print(p)
"""

persons_llm = extract_persons_llm(json_data["biography"], json_data["subject_name"])
print(persons_llm)

print()

build_rdf(persons_llm, json_data["subject_name"], json_data["person_id"])
visualize_rdf("output/knowledge_graph.ttl")

