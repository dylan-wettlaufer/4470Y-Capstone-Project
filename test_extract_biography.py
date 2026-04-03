import pytest
from unittest.mock import Mock, patch
import sys

sys.path.insert(0, '/mnt/user-data/uploads')

from extract_biography import (
    extract_info,
    extract_bio,
    extract_biblio,
    clean_text,
    extract_subject_name
)
from bs4 import BeautifulSoup

# Sample HTML fixtures
SAMPLE_BIOGRAPHY_HTML = """
<html>
<body>
    <section id="first" class="bio">
        <div id="bio-primary-image"><img src="portrait.jpg"></div>
        <p class="FirstParagraph"><strong>PEARSON, LESTER BOWLES</strong>, 
        diplomat and politician; b. 23 April 1897 in Toronto.</p>
        <p>He served as Prime Minister of Canada.</p>
    </section>
    <section id="second" class="biblio">
        <p>Archives of Canada. Dictionary of Canadian Biography.</p>
    </section>
</body>
</html>
"""

SAMPLE_HTML_NO_BIO = """
<html>
<body>
    <section id="second" class="biblio">
        <p>Only bibliography here.</p>
    </section>
</body>
</html>
"""

SAMPLE_HTML_NO_BIBLIO = """
<html>
<body>
    <section id="first" class="bio">
        <p class="FirstParagraph"><strong>TEST SUBJECT</strong></p>
        <p>Biography text here.</p>
    </section>
</body>
</html>
"""


class TestExtractInfo:
    """Black box tests for extract_info function, REQ-002"""

    @patch('extract_biography.requests.get')
    def test_extract_info_success(self, mock_get):
        """
        Black box test: Verify system extracts all fields from valid URL, REQ-002

        Test data: Valid DCB URL with complete HTML
        Expected: JSON with all required fields populated
        """
        mock_response = Mock()
        mock_response.text = SAMPLE_BIOGRAPHY_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"
        result = extract_info(url)

        # Verify all required fields exist
        assert result["url"] == url
        assert result["person_id"] == "pearson_lester_bowles_20E"
        assert result["subject_name"] == "PEARSON, LESTER BOWLES"
        assert "diplomat and politician" in result["biography"]
        assert "Prime Minister" in result["biography"]
        assert "Archives of Canada" in result["bibliography"]

    @patch('extract_biography.requests.get')
    def test_extract_info_removes_image_div(self, mock_get):
        """
        Black box test: Verify image divs are removed from biography

        Test data: HTML with bio-primary-image div
        Expected: Image div content not in biography text
        """
        mock_response = Mock()
        mock_response.text = SAMPLE_BIOGRAPHY_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://www.biographi.ca/en/bio/test.html"
        result = extract_info(url)

        # Image div should not appear in biography
        assert "bio-primary-image" not in result["biography"]
        assert "<img" not in result["biography"]

    @patch('extract_biography.requests.get')
    def test_extract_info_person_id_from_url(self, mock_get):
        """
        White box test: Verify person_id extraction from URL

        Code path: url.rstrip('/').split('/')[-1].replace('.html', '')
        """
        mock_response = Mock()
        mock_response.text = SAMPLE_BIOGRAPHY_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Test with .html extension
        url1 = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"
        result1 = extract_info(url1)
        assert result1["person_id"] == "pearson_lester_bowles_20E"

        # Test with trailing slash
        url2 = "https://www.biographi.ca/en/bio/smith_john_15A.html/"
        result2 = extract_info(url2)
        assert result2["person_id"] == "smith_john_15A"

    @patch('extract_biography.requests.get')
    def test_extract_info_http_error(self, mock_get):
        """
        Black box test: Verify HTTP errors are properly raised

        Test data: Mock response that raises HTTP error
        Expected: Exception propagated to caller
        """
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        url = "https://www.biographi.ca/en/bio/invalid.html"

        with pytest.raises(Exception) as exc_info:
            extract_info(url)

        assert "404 Not Found" in str(exc_info.value)


class TestExtractBio:
    """White box tests for extract_bio function"""

    def test_extract_bio_success(self):
        """
        White box test: Verify biography extraction from valid HTML

        Code path: find section → remove images → get_text → clean_text
        """
        soup = BeautifulSoup(SAMPLE_BIOGRAPHY_HTML, 'html.parser')
        result = extract_bio(soup)

        assert "PEARSON, LESTER BOWLES" in result
        assert "diplomat and politician" in result
        assert "Prime Minister" in result

    def test_extract_bio_removes_image_divs(self):
        """
        White box test: Verify image div removal logic

        Code path: bio_section.find_all("div", id="bio-primary-image") → decompose()
        """
        soup = BeautifulSoup(SAMPLE_BIOGRAPHY_HTML, 'html.parser')
        result = extract_bio(soup)

        # Image-related content should not appear
        assert "bio-primary-image" not in result
        assert "<img" not in result
        assert "portrait.jpg" not in result

    def test_extract_bio_section_not_found(self, capsys):
        """
        Black box test: Verify handling when biography section is missing

        Test data: HTML without biography section
        Expected: Empty string returned, error message printed
        """
        soup = BeautifulSoup(SAMPLE_HTML_NO_BIO, 'html.parser')
        result = extract_bio(soup)

        assert result == ""

        # Check console output
        captured = capsys.readouterr()
        assert "Biography section not found." in captured.out

    def test_extract_bio_applies_text_cleaning(self):
        """
        White box test: Verify clean_text is applied to biography, REQ-003

        Code path: bio_section.get_text() → clean_text(bio_text)
        """
        html = """
        <section id="first" class="bio">
            <p>Text with\xa0special\u2009spaces  and\n\nmultiple\nlines.</p>
        </section>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_bio(soup)

        # Special characters should be cleaned
        assert "\xa0" not in result
        assert "\u2009" not in result
        # Multiple newlines should be converted to single space
        assert "\n" not in result


class TestExtractBiblio:
    """White box tests for extract_biblio function"""

    def test_extract_biblio_success(self):
        """
        White box test: Verify bibliography extraction from valid HTML

        Code path: find section → get_text → clean_text
        """
        soup = BeautifulSoup(SAMPLE_BIOGRAPHY_HTML, 'html.parser')
        result = extract_biblio(soup)

        assert "Archives of Canada" in result
        assert "Dictionary of Canadian Biography" in result

    def test_extract_biblio_section_not_found(self, capsys):
        """
        Black box test: Verify handling when bibliography section is missing

        Test data: HTML without bibliography section
        Expected: Empty string returned, error message printed
        """
        soup = BeautifulSoup(SAMPLE_HTML_NO_BIBLIO, 'html.parser')
        result = extract_biblio(soup)

        assert result == ""

        # Check console output
        captured = capsys.readouterr()
        assert "Bibliography section not found." in captured.out

    def test_extract_biblio_applies_text_cleaning(self):
        """
        White box test: Verify clean_text is applied to bibliography, REQ-003

        Code path: biblio_section.get_text() → clean_text(biblio_text)
        """
        html = """
        <section id="second" class="biblio">
            <p>Reference\xa0with  spaces\nand lines.</p>
        </section>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_biblio(soup)

        # Text should be cleaned
        assert "\xa0" not in result
        assert "\n" not in result
        assert "  " not in result  # Multiple spaces normalized


class TestCleanText:
    """White box tests for clean_text function"""

    def test_clean_text_removes_special_spaces(self):
        """
        White box test: Verify removal of special Unicode space characters

        Code path: text.replace('\xa0', ' ') for each special space type
        """
        # Non-breaking space
        assert clean_text("Hello\xa0World") == "Hello World"

        # Thin space
        assert clean_text("Test\u2009Data") == "Test Data"

        # Zero-width space (removed completely)
        assert clean_text("No\u200bSpace") == "NoSpace"

        # Narrow no-break space
        assert clean_text("Text\u202fHere") == "Text Here"

    def test_clean_text_normalizes_multiple_spaces(self):
        """
        White box test: Verify multiple spaces normalized to single space

        Code path: re.sub(r' +', ' ', text)
        """
        assert clean_text("Hello    World") == "Hello World"
        assert clean_text("One  Two   Three    Four") == "One Two Three Four"
        assert clean_text("Tab        Space") == "Tab Space"

    def test_clean_text_handles_newlines(self):
        """
        White box test: Verify newline handling

        Code path: re.sub(r' *\n *', '\n', text) → text.replace('\n', ' ')
        """
        # Single newline
        assert clean_text("Line1\nLine2") == "Line1 Line2"

        # Multiple newlines
        assert clean_text("Line1\n\nLine2") == "Line1 Line2"

        # Newlines with spaces around them
        assert clean_text("Text  \n  More") == "Text More"

    def test_clean_text_strips_edges(self):
        """
        White box test: Verify leading/trailing whitespace removal

        Code path: return text.strip()
        """
        assert clean_text("  Text  ") == "Text"
        assert clean_text("\n\nText\n\n") == "Text"
        assert clean_text("   ") == ""

    def test_clean_text_combined_operations(self):
        """
        Regression test: Verify all cleaning operations work together

        This is a regression test ensuring all text cleaning features
        continue to work after code changes
        """
        # Complex text with multiple issues
        text = "  Hello\xa0World\n\nNext\u2009Line  with   spaces\u200b  "
        expected = "Hello World Next Line with spaces"
        assert clean_text(text) == expected

    def test_clean_text_empty_input(self):
        """
        Black box test: Verify handling of empty input
        """
        assert clean_text("") == ""
        assert clean_text("   ") == ""
        assert clean_text("\n\n\n") == ""


class TestExtractSubjectName:
    """White box tests for extract_subject_name function"""

    def test_extract_subject_name_success(self):
        """
        White box test: Verify subject name extraction from valid HTML

        Code path: find bio section → find FirstParagraph → find strong tag → get_text
        """
        soup = BeautifulSoup(SAMPLE_BIOGRAPHY_HTML, 'html.parser')
        result = extract_subject_name(soup)

        assert result == "PEARSON, LESTER BOWLES"

    def test_extract_subject_name_no_bio_section(self):
        """
        Black box test: Verify handling when bio section doesn't exist

        Test data: HTML without bio section
        Expected: None returned
        """
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_subject_name(soup)

        assert result is None

    def test_extract_subject_name_no_first_paragraph(self):
        """
        White box test: Verify handling when FirstParagraph class doesn't exist

        Code path: bio_section.find("p", class_="FirstParagraph") returns None
        """
        html = """
        <section id="first" class="bio">
            <p>Regular paragraph without FirstParagraph class</p>
        </section>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_subject_name(soup)

        assert result is None

    def test_extract_subject_name_no_strong_tag(self):
        """
        White box test: Verify handling when strong tag doesn't exist

        Code path: first_para.find("strong") returns None
        """
        html = """
        <section id="first" class="bio">
            <p class="FirstParagraph">Name without strong tag</p>
        </section>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_subject_name(soup)

        assert result is None

    def test_extract_subject_name_strips_whitespace(self):
        """
        White box test: Verify whitespace is stripped from subject name

        Code path: strong_tag.get_text(strip=True)
        """
        html = """
        <section id="first" class="bio">
            <p class="FirstParagraph"><strong>  SMITH, JOHN  </strong></p>
        </section>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_subject_name(soup)

        assert result == "SMITH, JOHN"
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_extract_subject_name_various_formats(self):
        """
        Black box test: Verify extraction works with different name formats
        """
        test_cases = [
            ("<strong>SMITH, JOHN</strong>", "SMITH, JOHN"),
            ("<strong>MARY JANE WATSON</strong>", "MARY JANE WATSON"),
            ("<strong>O'BRIEN, PATRICK</strong>", "O'BRIEN, PATRICK"),
            ("<strong>ST. LAURENT, LOUIS</strong>", "ST. LAURENT, LOUIS"),
        ]

        for strong_content, expected_name in test_cases:
            html = f"""
            <section id="first" class="bio">
                <p class="FirstParagraph">{strong_content}, description</p>
            </section>
            """
            soup = BeautifulSoup(html, 'html.parser')
            result = extract_subject_name(soup)
            assert result == expected_name


class TestIntegration:
    """Integration tests verifying components work together"""

    @patch('extract_biography.requests.get')
    def test_full_extraction_pipeline(self, mock_get):
        """
        Integration test: Verify all extraction functions work together

        Test data: Complete DCB HTML page
        Expected: All components extract their parts correctly
        """
        mock_response = Mock()
        mock_response.text = SAMPLE_BIOGRAPHY_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://www.biographi.ca/en/bio/pearson_lester_bowles_20E.html"
        result = extract_info(url)

        # Verify complete integration
        assert result["url"] == url
        assert result["person_id"] == "pearson_lester_bowles_20E"
        assert result["subject_name"] == "PEARSON, LESTER BOWLES"
        assert len(result["biography"]) > 0
        assert len(result["bibliography"]) > 0

        # Verify text was cleaned
        assert "\xa0" not in result["biography"]
        assert "\n" not in result["biography"]

    @patch('extract_biography.requests.get')
    def test_extraction_with_missing_sections(self, mock_get):
        """
        Integration test: Verify graceful handling of missing sections, REQ-010

        Test data: HTML with only bibliography
        Expected: System continues, returns empty strings for missing data
        """
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML_NO_BIO
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://www.biographi.ca/en/bio/test.html"
        result = extract_info(url)

        # Should not crash, returns empty for missing data
        assert result["biography"] == ""
        assert result["subject_name"] is None
        assert len(result["bibliography"]) > 0  # Bibliography still extracted


class TestEdgeCases:
    """Black box tests for edge cases"""

    def test_clean_text_only_special_characters(self):
        """
        Black box test: Text with only special characters
        """
        text = "\xa0\u2009\u200b\u202f"
        result = clean_text(text)
        assert result == ""

    def test_extract_subject_name_empty_strong_tag(self):
        """
        Black box test: Empty strong tag
        """
        html = """
        <section id="first" class="bio">
            <p class="FirstParagraph"><strong></strong></p>
        </section>
        """
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_subject_name(soup)

        # Should return empty string (not None, since tag exists)
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])