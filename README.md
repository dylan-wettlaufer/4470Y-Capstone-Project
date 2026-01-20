
# Collective Biography and Historiography with AI

Project Description:

Using LLM-based techniques, create a system to extract structured knowledge about biographical and bibliographical information from the online Dictionary of Canadian Biography (https://www.biographi.ca/en/). This will allow human and AI explorers to discover new historical patterns that emerge from considering the interrelationships of the lives of more than 9000 individuals who have played a role in Canadian History.



## Features Completed

- Scrapes biography and bibliography sections from the DCB website.
- Uses OpenAI LLM to extract:
  - Person names
  - Relationships to the subject (e.g., parent, child, spouse, colleague)
  - Roles/occupations
- Converts extracted data into RDF triples using FOAF, BIO, and relationship ontologies.
- Generates URIs for all persons and relationships.
- Ready for querying and further graph analysis.


## Run Locally

### Clone the repository

```bash
git clone <repo-url>
```

Go to the project directory

```bash
cd 4470Y-Capstone-Project
```

### Create virtual enviroment

```bash
python -m venv .venv
```

Activate virtual enviroment

```bash
source .venv/bin/activate

```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create a .env in the project root
Add OpenAI API key to .env

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Run the main script

```bash
python main.py
```

