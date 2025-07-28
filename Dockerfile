# Step 1: Use a specific, lightweight Python base image compatible with AMD64
FROM --platform=linux/amd64 python:3.9-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Set environment variables for container-specific paths.
# The modified main.py will use these paths when run inside Docker.
ENV INPUT_DIR=/app/input
ENV OUTPUT_DIR=/app/output

# Step 3: Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Step 4: Install the Python dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Pre-download and cache all required language models for offline use
# Download the sentence-transformer model for ranking.py
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L12-v2')"

# Download the T5 model for summarizer.py and content_refiner.py
RUN python -c "from transformers import T5Tokenizer, T5ForConditionalGeneration; \
               T5Tokenizer.from_pretrained('t5-small'); \
               T5ForConditionalGeneration.from_pretrained('t5-small')"

# Step 6: Copy all of your project code into the container
COPY . .

# Step 7: Specify the command to run when the container starts
CMD ["python", "main.py"]