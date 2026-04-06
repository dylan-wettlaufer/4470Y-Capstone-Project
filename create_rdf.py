from rdflib import URIRef, Namespace, Literal, Graph, ConjunctiveGraph
from rdflib.namespace import RDF, FOAF
import re
import unicodedata
from events_rdf import add_events
from namespaces import BASE, BIO, REL, PROV, RTMN

""" This file is responsible for converting the extracted data into RDF triples using FOAF, BIO, and relationship ontologies.
    It also creates URIs for all persons and relationships.
"""

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


def build_rdf(persons_json, subject_name, person_id, bio_url, events_json):
    """ Builds an RDF graph from the given persons_json, subject_name, and person_id 
    
    Args:
        persons_json (dict): Dictionary containing the extracted data
        subject_name (str): Name of the subject
        person_id (str): ID of the subject
    
    Returns:
        g (Graph): RDF graph containing the extracted data
    """

    g = ConjunctiveGraph() # use a conjuctive graph for named graphs

    g.bind("foaf", FOAF)
    g.bind("bio", BIO)
    g.bind("rel", REL)

    g.bind("prov", PROV)
    g.bind("rtmn", RTMN)

    factoid_counter = 1 

    subject_uri = create_person_uri(normalize_name(subject_name)) # create uri for the subject of the biography (ex. pearson)

    source_node = URIRef(RTMN + f"{normalize_name(subject_name)}_bio") # create uri for the source of the biography (ex. pearson_bio)
    ng = g.get_context(source_node) 
    
    ng.add((source_node, RTMN.sourceURL, Literal(bio_url))) # add the source biography url to the source node
    
    ng.add((subject_uri, RDF.type, FOAF.Person)) # add the subject to the graph
    ng.add((subject_uri, FOAF.name, Literal(normalize_name(subject_name)))) # add the subject name to the graph
    
    for person in persons_json["persons"]: # create a RDF object for each person
        person_uri = create_person_uri(person["name"])
        
        ng.add((person_uri, RDF.type, FOAF.Person)) # define the type of the person
        ng.add((person_uri, FOAF.name, Literal(normalize_name(person["name"])))) # add the person name to the graph

        # Handle relationships with correct direction
        for rel in person.get("relation_to_subject", []):

            factoid_uri = URIRef(RTMN + person_id + f"_Factoid_{factoid_counter}") # create a factoid for the relationship, tagged with person_id and factoid #
            factoid_counter += 1
            
            if rel in FORWARD_REL_MAP: # if the relationship is a forward relationship
                predicate = FORWARD_REL_MAP[rel]

                ng.add((factoid_uri, RDF.type, RTMN.Factoid)) # define the type of the factoid
                ng.add((factoid_uri, RDF.subject, subject_uri)) # add the subject to the factoid
                ng.add((factoid_uri, RDF.predicate, predicate)) # add the predicate to the factoid
                ng.add((factoid_uri, RDF.object, person_uri)) # add the object to the factoid
                ng.add((factoid_uri, PROV.wasDerivedFrom, source_node)) # add the source to the factoid
            
            elif rel in INVERSE_REL_MAP:
                predicate = INVERSE_REL_MAP[rel]
                
                ng.add((factoid_uri, RDF.type, RTMN.Factoid))
                ng.add((factoid_uri, RDF.subject, person_uri))
                ng.add((factoid_uri, RDF.predicate, predicate))
                ng.add((factoid_uri, RDF.object, subject_uri))
                ng.add((factoid_uri, PROV.wasDerivedFrom, source_node))
            
            # Default fallback
            else:
                ng.add((factoid_uri, RDF.type, RTMN.Factoid))
                ng.add((factoid_uri, RDF.subject, subject_uri))
                ng.add((factoid_uri, RDF.predicate, FOAF.knows))
                ng.add((factoid_uri, RDF.object, person_uri))
                ng.add((factoid_uri, PROV.wasDerivedFrom, source_node))
        
        # Add roles
        for role in person.get("roles", []):
            ng.add((person_uri, BIO.occupation, Literal(role)))

        # add events
        add_events(ng, events_json, subject_uri, source_node)

    g.serialize("output/" + person_id + "_" + "knowledge_graph.ttl", format="turtle")
    return person_id
