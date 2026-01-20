from extract_biography import extract_info
from ner import extract_persons, extract_persons_llm
from create_rdf import build_rdf
"""
Main file used to run the program.
Imports functions from other files to extract biographies and bibliographies, extract relationships with OpenAI LLM, and convert relationships to RDF triples
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

rdf_graph = build_rdf(persons_llm, json_data["subject_name"], json_data["person_id"])
print(rdf_graph.serialize(format="turtle"))
