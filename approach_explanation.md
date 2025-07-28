# Approach Explanation: Persona-Driven Document Intelligence Engine

This solution for Challenge 1b is a modular, offline-first system designed to extract the most relevant content from PDF documents based on a user’s persona and job-to-be-done. The entire workflow runs inside a Docker container with no internet access, ensuring data security and resource compliance.

### Step-by-Step Processing Pipeline

####  Step 1: Input Ingestion  
The system takes two inputs:
- A folder containing one or more PDF documents
- A `config.json` file specifying the persona and their job-to-be-done (the user’s query)

These inputs are mounted into the container and used to drive all downstream processing.

#### * Step 2: Structured Section Extraction (`pdf_processor.py`)  
Each PDF is parsed using the `PyMuPDF` library. The engine analyzes the layout to detect headers based on font size and weight differences compared to body text. Once identified, all text following a header is grouped under it. This transforms raw PDFs into a structured list of titled sections — each with a heading and its corresponding content.

#### * Step 3: Semantic Ranking (`ranking.py`)  
Each extracted section and the user query (persona + task) are converted into vector embeddings using the `all-MiniLM-L12-v2` sentence-transformer model. The system calculates cosine similarity between the query and each section to determine how semantically relevant the content is. This produces a ranked list, where higher scores indicate stronger alignment with the user’s intent.

#### * Step 4: Domain-Aware Filtering (`relevance_filter.py`)  
The initial ranked list is refined through rule-based filtering. The filter analyzes the query to determine the operational domain (e.g., academic, financial, culinary) and applies a dictionary of positive and negative keywords. Sections with undesirable terms (e.g., “chicken” in a vegetarian query) are penalized or excluded, while those with priority terms are boosted. This ensures strict adherence to user-defined constraints.

#### * Step 5: Final Output Generation (`main.py`)  
The top-ranked sections are selected for output. Instead of summarizing them, the system splits them into individual paragraphs and performs a final keyword check. Only the most relevant paragraphs — those containing terms aligned with the query — are included in the final JSON result.

### => Output:
The system generates a structured JSON file for each input PDF. Each file contains the most relevant multi-paragraph content, clearly aligned with the persona’s intent and requirements.

---

This pipeline ensures that every layer — from structural parsing to semantic ranking and domain filtering — works together to deliver high-quality, targeted document intelligence entirely offline.
