from rdflib import URIRef, Namespace, Literal, Graph
from rdflib.namespace import RDF, FOAF
import re
import unicodedata
""" This file is responsible for converting the extracted data into RDF triples using FOAF, BIO, and relationship ontologies.
    It also creates URIs for all persons and relationships.
"""

# Namespaces
BASE = Namespace("https://biographi.ca/person/")
BIO  = Namespace("https://biographi.ca/ontology/")
REL  = Namespace("http://purl.org/vocab/relationship/")

# Relationships that go FROM subject TO person
FORWARD_REL_MAP = {
    "child": REL.parentOf,           # Subject is parent of this person
    "spouse": REL.spouseOf,          # Symmetric - works either way
    "sibling": REL.siblingOf,        # Symmetric
    "descendant": BIO.ancestorOf,    # Subject is ancestor of this person
    "colleague": REL.colleagueOf,    # Symmetric
    "friend": REL.friendOf,          # Symmetric
    "mentor": REL.mentorOf          # Subject is mentor of this person
}

# Relationships that go FROM person TO subject (INVERSE)
INVERSE_REL_MAP = {
    "parent": REL.parentOf,          # This person is parent of subject
    "ancestor": BIO.ancestorOf,      # This person is ancestor of subject
    "opponent": BIO.opponentOf,      # This person is opponent of subject
    "monarch": BIO.reigningMonarch,  # This person is monarch over subject
}

def create_person_uri(name):
    """ Creates a URI for a person """
    return URIRef(BASE + name.lower().replace(" ", "_"))

def normalize_name(name):
    """ Normalizes a name by removing special characters and normalizing spaces """

    # Normalize Unicode (é → e)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Handle "Last, First Middle"
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2:
            name = parts[1] + " " + parts[0]

    # Remove titles and honorifics
    name = re.sub(r"\b(sir|lord|lady|rev|reverend|dr|hon|rt\. hon)\b", "", name, flags=re.I)

    # Remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Lowercase and underscore
    return name.lower().replace(" ", "_")


def build_rdf(persons_json, subject_name, person_id):
    """ Builds an RDF graph from the given persons_json, subject_name, and person_id 
    
    Args:
        persons_json (dict): Dictionary containing the extracted data
        subject_name (str): Name of the subject
        person_id (str): ID of the subject
    
    Returns:
        g (Graph): RDF graph containing the extracted data
    """

    g = Graph()

    g.bind("foaf", FOAF)
    g.bind("bio", BIO)
    g.bind("rel", REL)

    subject_uri = create_person_uri(person_id)
    
    g.add((subject_uri, RDF.type, FOAF.Person))
    g.add((subject_uri, FOAF.name, Literal(normalize_name(subject_name))))
    
    for person in persons_json["persons"]:
        person_uri = create_person_uri(person["name"])
        
        g.add((person_uri, RDF.type, FOAF.Person))
        g.add((person_uri, FOAF.name, Literal(normalize_name(person["name"]))))

        # Handle relationships with correct direction
        for rel in person.get("relation_to_subject", []):
            
            if rel in FORWARD_REL_MAP:
                predicate = FORWARD_REL_MAP[rel]
                g.add((subject_uri, predicate, person_uri))
            
            elif rel in INVERSE_REL_MAP:
                predicate = INVERSE_REL_MAP[rel]
                g.add((person_uri, predicate, subject_uri))  
            
            # Default fallback
            else:
                g.add((subject_uri, FOAF.knows, person_uri))
        
        # Add roles
        for role in person.get("roles", []):
            g.add((person_uri, BIO.occupation, Literal(role)))

    g.serialize("output/knowledge_graph.ttl", format="turtle")