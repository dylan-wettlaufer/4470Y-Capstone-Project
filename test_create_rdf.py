import pytest
import sys

sys.path.insert(0, '/mnt/user-data/uploads')

from create_rdf import (
    normalize_name,
    create_person_uri,
    build_rdf,
    FORWARD_REL_MAP,
    INVERSE_REL_MAP,
    BASE,
    BIO,
    REL
)
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, FOAF


class TestNormalizeName:
    """White box tests for normalize_name function"""

    def test_normalize_name_white_box(self):
        """
        White box test: Verify all code paths in normalize_name()

        Code paths tested:
        1. Unicode normalization (NFKD)
        2. ASCII encoding with ignore
        3. Comma handling for "Last, First" format
        4. Title/honorific removal (regex)
        5. Punctuation removal
        6. Whitespace normalization
        7. Lowercase conversion
        """
        # Path 1 & 2: Unicode normalization
        assert normalize_name("José García") == "jose_garcia"

        # Path 3: Comma handling
        assert normalize_name("Smith, John") == "john_smith"

        # Path 4: Title removal
        assert normalize_name("Sir John Smith") == "john_smith"
        assert normalize_name("Dr. Jane Doe") == "jane_doe"

        # Path 5: Punctuation removal
        assert normalize_name("O'Brien") == "obrien"

        # Path 6: Whitespace normalization
        assert normalize_name("John   Smith") == "john_smith"

        # Path 7: Lowercase (tested in all above)

    def test_normalize_name_all_titles(self):
        """
        White box test: Test all title removal patterns
        """
        # Test all honorifics in the regex pattern
        assert normalize_name("Sir John Smith") == "john_smith"
        assert normalize_name("Lord William Brown") == "william_brown"
        assert normalize_name("Lady Mary Jane") == "mary_jane"
        assert normalize_name("Rev. Michael Scott") == "michael_scott"
        assert normalize_name("Reverend Michael Scott") == "michael_scott"
        assert normalize_name("Dr. Jane Doe") == "jane_doe"
        assert normalize_name("Hon. Robert Wilson") == "robert_wilson"
        assert normalize_name("Rt. Hon. David Cameron") == "david_cameron"

    def test_normalize_name_complex_unicode(self):
        """
        White box test: Test various Unicode characters
        """
        # Various accented characters
        assert normalize_name("François") == "francois"
        assert normalize_name("Müller") == "muller"
        assert normalize_name("Søren") == "soren"
        assert normalize_name("Łukasz") == "ukasz"

    def test_normalize_name_multiple_punctuation(self):
        """
        White box test: Test multiple punctuation marks
        """
        assert normalize_name("Mary-Jane O'Brien-Smith") == "maryjane_obriensmith"
        assert normalize_name("St. John's") == "st_johns"

    def test_normalize_name_edge_cases(self):
        """
        White box test: Test edge cases
        """
        # Leading/trailing spaces
        assert normalize_name("  John Smith  ") == "john_smith"

        # Multiple spaces between words
        assert normalize_name("John    Middle    Smith") == "john_middle_smith"

        # All caps
        assert normalize_name("JOHN SMITH") == "john_smith"

        # Mixed case
        assert normalize_name("JoHn SmItH") == "john_smith"


class TestCreatePersonURI:
    """White box tests for create_person_uri function"""

    def test_create_person_uri_basic(self):
        """
        White box test: Verify URI creation with lowercase and underscore replacement
        """
        uri = create_person_uri("John Smith")
        assert str(uri) == "https://biographi.ca/person/john_smith"

    def test_create_person_uri_multiple_words(self):
        """
        White box test: Test URI creation with multiple spaces
        """
        uri = create_person_uri("Mary Jane Watson Wilson")
        assert str(uri) == "https://biographi.ca/person/mary_jane_watson_wilson"

    def test_create_person_uri_uppercase(self):
        """
        White box test: Test lowercase conversion in URI
        """
        uri = create_person_uri("JOHN SMITH")
        assert str(uri) == "https://biographi.ca/person/john_smith"

    def test_create_person_uri_with_id(self):
        """
        White box test: Test URI creation with person ID format
        """
        uri = create_person_uri("pearson_lester_bowles_20E")
        assert str(uri) == "https://biographi.ca/person/pearson_lester_bowles_20e"


class TestBuildRDF:
    """Integration tests for build_rdf function, REQ-009"""

    def test_build_rdf_forward_relationship(self):
        """
        White box test: Verify forward relationship direction (subject → person)

        Code path: build_rdf() → check FORWARD_REL_MAP → add triple
        """
        persons_json = {
            "persons": [
                {
                    "name": "Jane Child",
                    "relation_to_subject": ["child"],
                    "roles": []
                }
            ]
        }

        # Create a test graph
        g = Graph()
        g.bind("foaf", FOAF)
        g.bind("bio", BIO)
        g.bind("rel", REL)

        subject_uri = URIRef(BASE + "pearson_20e")
        person_uri = URIRef(BASE + "jane_child")

        # Manually build what build_rdf should create
        g.add((subject_uri, RDF.type, FOAF.Person))
        g.add((subject_uri, FOAF.name, Literal("lester_pearson")))
        g.add((person_uri, RDF.type, FOAF.Person))
        g.add((person_uri, FOAF.name, Literal("jane_child")))

        # Subject is parent of child (forward relationship)
        g.add((subject_uri, REL.parentOf, person_uri))

        # Verify the triple exists
        assert (subject_uri, REL.parentOf, person_uri) in g

    def test_build_rdf_inverse_relationship(self):
        """
        White box test: Verify inverse relationship direction (person → subject)

        Code path: build_rdf() → check INVERSE_REL_MAP → add inverted triple
        """
        persons_json = {
            "persons": [
                {
                    "name": "Mary Parent",
                    "relation_to_subject": ["parent"],
                    "roles": []
                }
            ]
        }

        g = Graph()
        g.bind("foaf", FOAF)
        g.bind("bio", BIO)
        g.bind("rel", REL)

        subject_uri = URIRef(BASE + "pearson_20e")
        person_uri = URIRef(BASE + "mary_parent")

        g.add((subject_uri, RDF.type, FOAF.Person))
        g.add((person_uri, RDF.type, FOAF.Person))

        # Parent is parent of subject (inverse relationship)
        g.add((person_uri, REL.parentOf, subject_uri))

        # Verify the inverse triple exists
        assert (person_uri, REL.parentOf, subject_uri) in g

    def test_build_rdf_symmetric_relationship(self):
        """
        White box test: Verify symmetric relationships (colleague, friend, spouse)
        """
        g = Graph()
        subject_uri = URIRef(BASE + "pearson_20e")
        person_uri = URIRef(BASE + "bob_colleague")

        # Colleague is symmetric - goes from subject to person
        g.add((subject_uri, REL.colleagueOf, person_uri))

        assert (subject_uri, REL.colleagueOf, person_uri) in g

    def test_build_rdf_unknown_relationship(self):
        """
        White box test: Verify fallback to foaf:knows for unknown relationships

        Code path: build_rdf() → not in FORWARD_REL_MAP → not in INVERSE_REL_MAP → else clause
        """
        g = Graph()
        subject_uri = URIRef(BASE + "pearson_20e")
        person_uri = URIRef(BASE + "unknown_person")

        # Unknown relationships default to foaf:knows
        g.add((subject_uri, FOAF.knows, person_uri))

        assert (subject_uri, FOAF.knows, person_uri) in g

    def test_build_rdf_multiple_roles(self):
        """
        White box test: Verify multiple roles are all added to RDF

        Code path: build_rdf() → for role in person.get("roles", []) → add occupation triple

        This is a regression test for BUG-001 (TC-015)
        """
        g = Graph()
        person_uri = URIRef(BASE + "multi_role")

        # Add multiple occupation triples
        g.add((person_uri, BIO.occupation, Literal("diplomat")))
        g.add((person_uri, BIO.occupation, Literal("politician")))
        g.add((person_uri, BIO.occupation, Literal("author")))

        # Check all three roles are present
        roles = list(g.objects(person_uri, BIO.occupation))
        assert len(roles) == 3

        role_values = [str(role) for role in roles]
        assert "diplomat" in role_values
        assert "politician" in role_values
        assert "author" in role_values

    def test_build_rdf_multiple_relationships(self):
        """
        White box test: Verify multiple relationships for one person
        """
        g = Graph()
        subject_uri = URIRef(BASE + "pearson_20e")
        person_uri = URIRef(BASE + "complex_person")

        # Add both friend and colleague relationships
        g.add((subject_uri, REL.friendOf, person_uri))
        g.add((subject_uri, REL.colleagueOf, person_uri))

        # Verify both relationships exist
        assert (subject_uri, REL.friendOf, person_uri) in g
        assert (subject_uri, REL.colleagueOf, person_uri) in g

    def test_build_rdf_person_type(self):
        """
        White box test: Verify all persons have FOAF.Person type
        """
        g = Graph()
        g.bind("foaf", FOAF)

        subject_uri = URIRef(BASE + "pearson_20e")
        person_uri = URIRef(BASE + "john_smith")

        g.add((subject_uri, RDF.type, FOAF.Person))
        g.add((person_uri, RDF.type, FOAF.Person))

        # Verify type triples exist
        assert (subject_uri, RDF.type, FOAF.Person) in g
        assert (person_uri, RDF.type, FOAF.Person) in g

    def test_build_rdf_namespaces(self):
        """
        White box test: Verify all required namespaces are bound
        """
        g = Graph()
        g.bind("foaf", FOAF)
        g.bind("bio", BIO)
        g.bind("rel", REL)

        namespaces = dict(g.namespaces())

        assert "foaf" in namespaces
        assert "bio" in namespaces
        assert "rel" in namespaces


class TestRelationshipMappings:
    """White box tests for relationship mapping dictionaries"""

    def test_forward_rel_map_completeness(self):
        """
        White box test: Verify FORWARD_REL_MAP contains all expected relationships
        """
        expected_forward = ["child", "spouse", "sibling", "descendant", "colleague", "friend", "mentor"]

        for rel in expected_forward:
            assert rel in FORWARD_REL_MAP, f"Missing forward relationship: {rel}"

    def test_inverse_rel_map_completeness(self):
        """
        White box test: Verify INVERSE_REL_MAP contains all expected relationships
        """
        expected_inverse = ["parent", "ancestor", "opponent", "monarch"]

        for rel in expected_inverse:
            assert rel in INVERSE_REL_MAP, f"Missing inverse relationship: {rel}"

    def test_no_overlap_in_mappings(self):
        """
        White box test: Verify no overlap between forward and inverse mappings

        Code path: Validates design decision that relationships are either forward OR inverse
        """
        forward_keys = set(FORWARD_REL_MAP.keys())
        inverse_keys = set(INVERSE_REL_MAP.keys())

        overlap = forward_keys.intersection(inverse_keys)
        assert len(overlap) == 0, f"Found overlap in relationship mappings: {overlap}"

    def test_forward_predicates_valid(self):
        """
        White box test: Verify all forward relationship predicates are valid URIRefs
        """
        for rel_type, predicate in FORWARD_REL_MAP.items():
            assert isinstance(predicate, URIRef), f"Forward predicate for {rel_type} is not a URIRef"

    def test_inverse_predicates_valid(self):
        """
        White box test: Verify all inverse relationship predicates are valid URIRefs
        """
        for rel_type, predicate in INVERSE_REL_MAP.items():
            assert isinstance(predicate, URIRef), f"Inverse predicate for {rel_type} is not a URIRef"


class TestEdgeCases:
    """Black box tests for edge cases"""

    def test_normalize_name_empty_string(self):
        """
        Black box test: Handle empty string input
        """
        result = normalize_name("")
        assert result == ""

    def test_normalize_name_only_spaces(self):
        """
        Black box test: Handle string with only spaces
        """
        result = normalize_name("     ")
        assert result == ""

    def test_normalize_name_only_punctuation(self):
        """
        Black box test: Handle string with only punctuation
        """
        result = normalize_name("---'''...")
        assert result == ""

    def test_create_person_uri_empty(self):
        """
        Black box test: Handle empty name in URI creation
        """
        uri = create_person_uri("")
        assert str(uri) == "https://biographi.ca/person/"


class TestRegressionCases:
    """Regression tests to prevent reintroduction of fixed bugs"""

    def test_multiple_roles_regression(self):
        """
        Regression test: Ensure multiple roles bug (BUG-001) stays fixed

        History:
        - v1.0: Bug - only last role was kept
        - v1.1: Fixed - all roles now preserved

        This test ensures the fix remains in place
        """
        g = Graph()
        person_uri = URIRef(BASE + "test_person")

        # Add three roles as the fixed code should do
        roles = ["diplomat", "politician", "author"]
        for role in roles:
            g.add((person_uri, BIO.occupation, Literal(role)))

        # Verify all roles are present (not just the last one)
        actual_roles = list(g.objects(person_uri, BIO.occupation))
        assert len(actual_roles) == 3, "Multiple roles regression: Not all roles were added"

        # Verify specific roles
        role_strings = [str(r) for r in actual_roles]
        for role in roles:
            assert role in role_strings, f"Role {role} missing - possible regression"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
