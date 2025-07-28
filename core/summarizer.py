from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import logging

class TextSummarizer:
    """
    Summarizes text using the T5-small model, guided by the user's original query
    to ensure the summary is relevant and detailed.
    """
    MODEL_NAME = 't5-small'

    def __init__(self):
        """
        Initializes the tokenizer and model for summarization.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"TextSummarizer using device: {self.device}")
        try:
            # Using legacy=False is recommended for new T5 usage
            self.tokenizer = T5Tokenizer.from_pretrained(self.MODEL_NAME, legacy=False)
            self.model = T5ForConditionalGeneration.from_pretrained(self.MODEL_NAME).to(self.device)
            logging.info(f"Summarization model '{self.MODEL_NAME}' loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load T5 model or tokenizer: {self.MODEL_NAME}")
            raise e

    def summarize(self, query: str, text: str) -> str:
        """
        Generates a concise, relevant summary for the given text, guided by the query.

        Args:
            query (str): The user's original request (e.g., "vegetarian dinner").
            text (str): The text content from a relevant page to summarize.

        Returns:
            str: The generated summary.
        """
        if not text:
            return ""

        # A more instructional prompt for better, context-aware summaries.
        prompt = (
            f"Based on the user's request for '{query}', provide a detailed summary of the "
            f"following text. Focus on the key ingredients, preparation steps, and any "
            f"details relevant to the request. Text to summarize: {text}"
        )
        
        inputs = self.tokenizer.encode(
            prompt,
            return_tensors='pt',
            max_length=1024, # Use a larger context window
            truncation=True
        ).to(self.device)

        # Generate a longer, more descriptive summary
        summary_ids = self.model.generate(
            inputs,
            max_length=200,   # Target a longer summary
            min_length=70,    # Ensure it's not too brief
            length_penalty=2.5, # Encourage detail
            num_beams=4,
            early_stopping=True
        )

        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        return summary