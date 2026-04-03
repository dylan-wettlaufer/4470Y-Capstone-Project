import re
import os
from dotenv import load_dotenv
import json
from openai import OpenAI

load_dotenv()

def parse_bibliography_llm(biblio_text):
    # create system prompt for bibliography extraction
    """ Extract bibliography entries using OpenAI LLM 
    args:
        biblio_text (str): The bibliography text to extract entries from
    returns:
        json: A json of bibliography entries with structured data
    """
    
    system_prompt = """
    You are extracting comprehensive bibliography data from the Dictionary of Canadian Biography for academic research.

    TASK:
    Extract ALL bibliography entries with maximum detail for Zotero import and scholarly use.

    For each entry, return:
    1. Type of publication
    2. Author name(s) - format as "Last, First Middle"
    3. Title of work - complete title
    4. Year of publication
    5. Publisher - full publisher name
    6. Address/City - publication location
    7. ISBN - if available
    8. Pages - page count or page range
    9. Series - series title if applicable
    10. Volume - volume number
    11. Number - series/issue number
    12. Edition - edition information
    13. Editor - editor name(s) if different from author
    14. Translator - translator name(s) if applicable
    15. Keywords - relevant subject keywords
    16. Abstract - brief summary if available
    17. Note - additional details like "Reprinted with new introduction"

    ALLOWED TYPES:
    book, article, archive, government_document, thesis, manuscript, book_chapter, conference_paper, newspaper_article, other

    RULES:
    - Extract ALL references mentioned with maximum detail
    - Format author names as "Last, First" for proper BibTeX
    - Extract publisher names, not just cities (e.g., "University of Toronto Press" not just "Toronto")
    - Look for ISBN numbers, page counts, series information
    - Include editors, translators, edition information
    - Do NOT invent information - leave empty if not found
    - If unsure about any field, leave as "" (empty string)
    - List each entry only once
    - Do NOT include explanations or prose

    RETURN FORMAT (valid JSON only):

    {
    "entries": [
        {
        "type": "book",
        "author": "Pearson, Lester B.",
        "title": "Words and occasions: an anthology of speeches and articles selected from his papers",
        "year": "1970",
        "publisher": "University of Toronto Press",
        "address": "Toronto",
        "isbn": "",
        "pages": "xiv, 312",
        "series": "The Carleton Library Series",
        "volume": "",
        "number": "92",
        "edition": "",
        "editor": "",
        "translator": "",
        "keywords": "",
        "abstract": "",
        "note": "Selected and edited with an introduction by the author"
        }
    ]
    }
    """

    user_prompt = biblio_text

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o",   
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    # store response to load into json
    text_response = response.choices[0].message.content

    try:
        return json.loads(text_response)
    except json.JSONDecodeError:
        print("Failed to parse JSON from OpenAI output")
        print(text_response)
        return {"entries": []}


def convert_llm_to_bibtex(llm_entries, filename="output/bibliography.bib"):
    """Convert LLM-structured entries to comprehensive BibTeX format"""
    
    bibtex_entries = []
    
    for i, entry in enumerate(llm_entries.get('entries', [])):
        # create citation key
        key = f"ref_{i+1}"
        if entry.get('author') and entry.get('author') != "Unknown":
            # handle "Last, First" format properly
            author_parts = entry['author'].split(',')
            if len(author_parts) >= 2:
                last_name = author_parts[0].strip().lower().replace(' ', '')
                key = f"{last_name}_{entry.get('year', i+1)}"
            else:
                last_name = entry['author'].split()[-1].lower()
                key = f"{last_name}_{entry.get('year', i+1)}"
        
        # choose BibTeX type based on entry type
        entry_type = entry.get('type', 'book').lower()
        bibtex_type_mapping = {
            'article': 'article',
            'thesis': 'phdthesis',
            'book_chapter': 'incollection',
            'conference_paper': 'inproceedings',
            'newspaper_article': 'article',
            'archive': 'misc',
            'government_document': 'misc',
            'manuscript': 'misc',
            'other': 'misc'
        }
        bibtex_type = bibtex_type_mapping.get(entry_type, 'book')
        
        #create BibTeX entry
        bibtex = f"@{bibtex_type}{{{key},\n"
        
        #standard fields to have
        if entry.get('author') and entry.get('author') != "Unknown":
            bibtex += f"    author = {{{entry['author']}}},\n"
            
        if entry.get('title'):
            bibtex += f"    title = {{{entry['title']}}},\n"
            
        if entry.get('year'):
            bibtex += f"    year = {{{entry['year']}}},\n"
        
        if entry.get('publisher'):
            bibtex += f"    publisher = {{{entry['publisher']}}},\n"
            
        if entry.get('address'):
            bibtex += f"    address = {{{entry['address']}}},\n"
            
        if entry.get('isbn'):
            bibtex += f"    isbn = {{{entry['isbn']}}},\n"
            
        if entry.get('pages'):
            bibtex += f"    pages = {{{entry['pages']}}},\n"
            
        if entry.get('series'):
            bibtex += f"    series = {{{entry['series']}}},\n"
            
        if entry.get('volume'):
            bibtex += f"    volume = {{{entry['volume']}}},\n"
            
        if entry.get('number'):
            bibtex += f"    number = {{{entry['number']}}},\n"
            
        if entry.get('edition'):
            bibtex += f"    edition = {{{entry['edition']}}},\n"
            
        if entry.get('editor'):
            bibtex += f"    editor = {{{entry['editor']}}},\n"
            
        if entry.get('translator'):
            bibtex += f"    translator = {{{entry['translator']}}},\n"
            
        if entry.get('keywords'):
            bibtex += f"    keywords = {{{entry['keywords']}}},\n"
            
        if entry.get('abstract'):
            bibtex += f"    abstract = {{{entry['abstract']}}},\n"
            
        # note field for additional details
        note_fields = []
        if entry.get('note'):
            note_fields.append(entry['note'])
        if entry.get('details'):
            note_fields.append(entry['details'])
        
        if note_fields:
            bibtex += f"    note = {{{'; '.join(note_fields)}}},\n"
            
        bibtex += "}"
        
        bibtex_entries.append(bibtex)
    
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in bibtex_entries:
            f.write(entry + "\n\n")
    
    print(f"Comprehensive LLM Bibliography saved to {filename}")
    print(f"Created {len(bibtex_entries)} enhanced BibTeX entries")
