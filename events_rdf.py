from rdflib import URIRef, Literal
from rdflib.namespace import RDF
from rdflib.namespace import FOAF
from namespaces import RTMN, PROV, BIO

def normalize_string(s):
    """Normalize strings to be URI-safe."""
    import re, unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s.lower()

def add_events(graph_context, events_json, subject_uri, source_uri):
    """
    Adds events to the RDF graph as rtmn:Event triples.

    Args:
        graph_context: RDFLib context (ConjunctiveGraph context) to add triples to
        events_json: JSON object returned by extract_events_llm
        subject_uri: URI of the person the events are about
        source_uri: URI representing the source document (biography)
    """
    event_counter = 1 # counter for events
    for event in events_json.get("events", []):
        # Create a URI for this event
        event_label = normalize_string(f"{subject_uri.split('/')[-1]}_{event_counter}_{event.get('event_type','other')}")
        event_uri = URIRef(RTMN + event_label)
        event_counter += 1

        # Add the event itself
        graph_context.add((event_uri, RDF.type, RTMN.Event))
        graph_context.add((event_uri, RTMN.aboutPerson, subject_uri))
        graph_context.add((event_uri, PROV.wasDerivedFrom, source_uri))

        # Add event properties
        if event.get("description"):
            graph_context.add((event_uri, RTMN.description, Literal(event["description"])))
        if event.get("date"):
            graph_context.add((event_uri, RTMN.date, Literal(event["date"])))
        if event.get("place"):
            graph_context.add((event_uri, RTMN.place, Literal(event["place"])))
        if event.get("event_type"):
            graph_context.add((event_uri, RTMN.eventType, Literal(event["event_type"])))