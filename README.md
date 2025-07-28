# Adobe Hackathon 2025 - Persona-Driven Document Intelligence Engine

This project is a solution for Challenge 1b, designed to extract and prioritize relevant information from PDFs based on a given persona and job-to-be-done.  
*This solution combines structured parsing with semantic AI — offline, secure, and purpose-driven.*

## Approach

The solution follows a clean, modular, and multi-stage pipeline:

<pre>
pdf_processor.py      →      ranking.py      →      relevance_filter.py      →      main.py

[Extract sections         [Rank by semantic         [Re-rank using domain         [Extract relevant
 from headers]             similarity to query]      rules & filters]              paragraphs]
</pre>

Each module is laser-focused on a specific task:

•⁠  ⁠*pdf_processor.py*  
  Parses PDF structure and identifies headers based on font contrast. Groups body text under each heading to form titled sections.

•⁠  ⁠*ranking.py*  
  Uses the ⁠ all-MiniLM-L12-v2 ⁠ model to embed section content and persona-based query. Computes cosine similarity for semantic relevance.

•⁠  ⁠*relevance_filter.py*  
  Applies domain-aware rule-based filtering to adjust rankings. Penalizes irrelevant or contradictory content and boosts important keywords.

•⁠  ⁠*main.py* – Runs the final extraction pass. Splits top-ranked sections into paragraphs and includes all that are relevant to the user's query.

=> This step-by-step architecture ensures highly relevant, multi-paragraph outputs tailored to user intent.

## Models and Libraries Used

•⁠  ⁠*Language:* Python 3.9  
•⁠  ⁠*PDF Processing:* PyMuPDF  
•⁠  ⁠*NLP & Semantic Ranking:* sentence-transformers, PyTorch (CPU)  
•⁠  ⁠*Core Model:* all-MiniLM-L12-v2 (~134 MB)  
•⁠  ⁠*Containerization:* Docker  

## How to Build and Run

The solution is containerized with Docker and has no external network dependencies at runtime.

### *->Build the Docker Image*

Use the following command from the root of the project directory:

⁠ bash
docker build --platform linux/amd64 -t mysolution:latest .
 ⁠

### *->Run the Container*

*To process PDFs, place them in the ⁠ input ⁠ directory. The container will automatically process all PDFs and place the corresponding JSON files in the ⁠ output ⁠ directory.*

Use the following command to run the container, replacing ⁠ $(pwd) ⁠ with the absolute path to your project directory if you are not using a Unix-like shell.

⁠ bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolution:latest
