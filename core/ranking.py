import torch
from sentence_transformers import SentenceTransformer, util
import logging

class SectionRanker:
    """
    Ranks text sections based on semantic similarity to a query.
    """
    MODEL_NAME = 'sentence-transformers/all-MiniLM-L12-v2'

    def __init__(self):
        """
        Initializes the SectionRanker, loading the embedding model.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"SectionRanker using device: {self.device}")
        
        try:
            self.model = SentenceTransformer(self.MODEL_NAME, device=self.device)
            logging.info(f"Ranking model '{self.MODEL_NAME}' loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load sentence transformer model: {self.MODEL_NAME}")
            raise e

    def rank_sections(self, query: str, sections: list) -> list:
        """
        Ranks a list of text sections based on their semantic similarity to a query.

        Args:
            query (str): The search query (e.g., persona + job description).
            sections (list of dicts): A list of section dictionaries. Each dict
                                      must have a 'content' key.

        Returns:
            list of dicts: The input list of sections, sorted by relevance,
                           with a 'similarity_score' key added.
        """
        if not sections:
            return []

        section_contents = [sec.get('content', '') for sec in sections]

        logging.info(f"Encoding query and {len(section_contents)} sections for ranking...")
        query_embedding = self.model.encode(query, convert_to_tensor=True, device=self.device)
        section_embeddings = self.model.encode(section_contents, convert_to_tensor=True, device=self.device)
        
        # Compute cosine similarity between the query and all sections
        cosine_scores = util.cos_sim(query_embedding, section_embeddings)[0]

        # Add the calculated score to each section's dictionary
        for i, section in enumerate(sections):
            section['similarity_score'] = cosine_scores[i].item()

        # Sort all sections by their similarity score in descending order
        ranked_sections = sorted(sections, key=lambda x: x['similarity_score'], reverse=True)
        logging.info("Ranking complete.")
        
        return ranked_sections
