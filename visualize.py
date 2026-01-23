from rdflib import Graph
from pyvis.network import Network
"""
Visualize RDF triples as a network graph.
"""

HTML_OUT = "output/knowledge_graph.html"

def visualize_rdf(ttl_path: str):
    g = Graph() # Create an empty RDF graph
    g.parse(ttl_path, format="turtle") # Parse the TTL file to set graph
    
    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white", directed=True) # Create a network graph
    
    # Add nodes and edges
    for s, p, o in g:
        s_str = str(s)
        o_str = str(o)
        p_str = p.split("/")[-1]  # retrieve edge labels

        # Add nodes 
        net.add_node(s_str, label=s_str.split("/")[-1])
        net.add_node(o_str, label=o_str.split("/")[-1])

        # Add edge with predicate label
        net.add_edge(s_str, o_str, title=p_str, label=p_str)
    
    net.write_html(HTML_OUT) # Write the network graph to an HTML file
    print(f"Visualization saved to {HTML_OUT}") 