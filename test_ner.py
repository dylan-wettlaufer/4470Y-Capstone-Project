import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import sys

sys.path.insert(0, '/mnt/user-data/uploads')

from ner import extract_persons, clean_person_names, extract_persons_llm

class TestCleanPersonNames:
    """Test person name cleaning functionality"""

    def test_clean_person_names_removes_possessives(self):
        """Test removal of possessive markers"""
        persons = ["John's", "Jane's house", "Bob Smith's"]
        result = clean_person_names(persons, 1)

        assert "John" in result
        assert "Jane house" in result
        assert "Bob Smith" in result

    def test_clean_person_names_filters_by_word_count(self):
        """Test filtering by minimum word count"""
        persons = ["John", "Jane Doe", "Bob Smith Wilson"]

        result_min_1 = clean_person_names(persons, 1)
        assert "John" in result_min_1
        assert "Jane Doe" in result_min_1

        result_min_2 = clean_person_names(persons, 2)
        assert "John" not in result_min_2
        assert "Jane Doe" in result_min_2
        assert "Bob Smith Wilson" in result_min_2

    def test_clean_person_names_deduplicates(self):
        """Test deduplication of names"""
        persons = ["John Smith", "Jane Doe", "John Smith"]
        result = clean_person_names(persons, 2)

        assert result.count("John Smith") == 1

    def test_clean_person_names_sorts(self):
        """Test that results are sorted"""
        persons = ["Zara Wilson", "Alice Brown", "Michael Scott"]
        result = clean_person_names(persons, 2)

        assert result == sorted(result)

    def test_clean_person_names_strips_whitespace(self):
        """Test that whitespace is stripped"""
        persons = ["  John Smith  ", "Jane Doe"]
        result = clean_person_names(persons, 2)

        assert "John Smith" in result
        assert "  John Smith  " not in result


class TestExtractPersonsLLM:
    """Test OpenAI LLM-based person extraction"""

    @patch('ner.OpenAI')
    @patch('ner.os.getenv')
    def test_extract_persons_llm_success(self, mock_getenv, mock_openai):
        """Test successful LLM extraction"""
        mock_getenv.return_value = "fake-api-key"

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()

        expected_json = {
            "persons": [
                {
                    "name": "John Smith",
                    "relation_to_subject": ["colleague"],
                    "roles": ["diplomat"]
                }
            ]
        }

        mock_message.content = json.dumps(expected_json)
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        biography_text = "John Smith was a colleague and diplomat."
        subject_name = "Lester Pearson"

        result = extract_persons_llm(biography_text, subject_name)

        assert result == expected_json
        assert len(result["persons"]) == 1
        assert result["persons"][0]["name"] == "John Smith"

    @patch('ner.OpenAI')
    @patch('ner.os.getenv')
    def test_extract_persons_llm_system_prompt_includes_subject(self, mock_getenv, mock_openai):
        """Test that system prompt includes subject name"""
        mock_getenv.return_value = "fake-api-key"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"persons": []}'
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        subject_name = "Lester Pearson"
        extract_persons_llm("Some text", subject_name)

        # Check that the API was called
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        system_message = messages[0]['content']

        assert subject_name in system_message

    @patch('ner.OpenAI')
    @patch('ner.os.getenv')
    def test_extract_persons_llm_uses_correct_model(self, mock_getenv, mock_openai):
        """Test that correct model is used"""
        mock_getenv.return_value = "fake-api-key"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"persons": []}'
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        extract_persons_llm("Some text", "Subject")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4o"
        assert call_args[1]['temperature'] == 0
        assert call_args[1]['response_format'] == {"type": "json_object"}

    @patch('ner.OpenAI')
    @patch('ner.os.getenv')
    def test_extract_persons_llm_json_decode_error(self, mock_getenv, mock_openai, capsys):
        """Test handling of invalid JSON response"""
        mock_getenv.return_value = "fake-api-key"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Invalid JSON {{{{"
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        result = extract_persons_llm("Some text", "Subject")

        assert result == {"persons": []}
        captured = capsys.readouterr()
        assert "Failed to parse JSON" in captured.out

    @patch('ner.OpenAI')
    @patch('ner.os.getenv')
    def test_extract_persons_llm_allowed_relationships(self, mock_getenv, mock_openai):
        """Test that system prompt includes all allowed relationship types"""
        mock_getenv.return_value = "fake-api-key"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"persons": []}'
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        extract_persons_llm("Some text", "Subject")

        call_args = mock_client.chat.completions.create.call_args
        system_message = call_args[1]['messages'][0]['content']

        expected_relations = [
            "parent", "child", "spouse", "sibling", "ancestor", "descendant",
            "political_associate", "colleague", "superior", "subordinate",
            "mentor", "opponent", "monarch", "friend", "other"
        ]

        for relation in expected_relations:
            assert relation in system_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])