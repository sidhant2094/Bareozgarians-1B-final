from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import logging

class ContentRefiner:
    """
    Uses the T5 model to intelligently elaborate on text, creating a
    detailed, readable paragraph based on the user's query.
    """
    MODEL_NAME = 't5-small'

    def __init__(self):
        """
        Initializes the tokenizer and model.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"ContentRefiner using device: {self.device}")
        try:
            self.tokenizer = T5Tokenizer.from_pretrained(self.MODEL_NAME, legacy=False)
            self.model = T5ForConditionalGeneration.from_pretrained(self.MODEL_NAME).to(self.device)
            logging.info(f"ContentRefiner model '{self.MODEL_NAME}' loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load T5 model or tokenizer: {self.MODEL_NAME}")
            raise e

    def refine_text(self, query: str, text: str) -> str:
        """
        Generates a detailed, query-focused paragraph from the source text.
        """
        if not text:
            return ""

        prompt = (
            f"Based on the user's request for '{query}', extract the most relevant information from the following text. "
            f"Combine the key points into a comprehensive and detailed paragraph of 120-150 words. Do not just list facts, "
            f"but explain them in a readable and informative way. Text: {text}"
        )
        
        inputs = self.tokenizer.encode(
            prompt,
            return_tensors='pt',
            max_length=1024,
            truncation=True
        ).to(self.device)

        refined_text_ids = self.model.generate(
            inputs,
            max_length=350,
            min_length=120,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        refined_text = self.tokenizer.decode(refined_text_ids[0], skip_special_tokens=True)
        return refined_text
