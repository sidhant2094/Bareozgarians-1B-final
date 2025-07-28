import re
import logging

# --- Domain-Specific Keyword Dictionaries ---
# These dictionaries provide the filter with domain-specific knowledge.
DOMAIN_KEYWORDS = {
    'academic': {
        'positive': {'methodology', 'dataset', 'benchmark', 'results', 'conclusion', 'abstract', 
                     'introduction', 'literature', 'review', 'study', 'experiment', 'validation'},
        'negative': {'appendix', 'references', 'acknowledgments', 'biography'}
    },
    'financial': {
        'positive': {'revenue', 'profit', 'loss', 'ebitda', 'margin', 'investment', 'r&d', 'assets',
                     'liabilities', 'equity', 'cash flow', 'outlook', 'guidance', 'market share', 
                     'strategy', 'risk', 'trends'},
        'negative': {'legal disclaimer', 'forward-looking statements', 'table of contents'}
    },
    'technical': {
        'positive': {'create', 'manage', 'fillable', 'form', 'onboarding', 'compliance', 'tutorial', 
                     'how-to', 'guide', 'steps', 'instructions', 'configuration', 'setup'},
        'negative': {'marketing', 'overview', 'pricing', 'advertisement'}
    },
    'culinary': {
        'positive': {'vegetarian', 'vegan', 'dinner', 'lunch', 'breakfast', 'dessert', 'appetizer',
                     'side dish', 'gluten-free', 'recipe', 'ingredients', 'instructions'},
        'negative': {'beef', 'pork', 'chicken', 'lamb', 'turkey', 'veal', 'duck', 'sausage', 
                     'bacon', 'ham', 'sirloin', 'steak', 'mince', 'patty', 'fillet', 'fish', 
                     'salmon', 'tuna', 'shrimp', 'prawn', 'crab', 'lobster', 'oyster'}
    }
}

class RelevanceFilter:
    """
    Applies a dynamic, domain-aware set of rules to re-rank and filter sections,
    ensuring strict adherence to user requirements across various domains.
    """
    def __init__(self, query: str):
        self.query_lower = query.lower()
        self.domain = self._identify_domain()
        
        self.positive_keywords = self._extract_positive_keywords()
        self.negative_keywords = self._extract_negative_keywords()
        self.distractor_titles = self._get_distractor_titles()

        logging.info(f"RelevanceFilter initialized for domain: '{self.domain}'.")
        logging.info(f"Positive Keywords: {self.positive_keywords}")
        logging.info(f"Negative Keywords: {self.negative_keywords}")
        logging.info(f"Distractor Titles: {self.distractor_titles}")

    def _identify_domain(self) -> str:
        """Identifies the most likely domain based on query keywords."""
        for domain, keywords in DOMAIN_KEYWORDS.items():
            # Check against both positive and negative keywords for a robust match
            if any(kw in self.query_lower for kw in keywords['positive']) or \
               any(kw in self.query_lower for kw in keywords['negative']):
                return domain
        return 'general' # Default domain if none match

    def _extract_positive_keywords(self) -> set:
        """Extracts all nouns and adjectives from the query as positive keywords."""
        # A simple regex to find sequences of words that are likely concepts
        words = set(re.findall(r'\b[a-z][a-z-]{2,}\b', self.query_lower))
        stop_words = {'prepare', 'provide', 'analyze', 'identify', 'summarize', 'focusing', 'review', 
                      'for', 'and', 'the', 'with', 'from', 'based', 'on', 'using', 'given', 'acting', 
                      'as', 'a', 'an', 'of', 'in', 'to', 'is', 'are'}
        return words - stop_words

    def _extract_negative_keywords(self) -> set:
        """Extracts hard negative constraints from the query and domain."""
        negatives = set()
        # Add domain-specific negatives
        if self.domain in DOMAIN_KEYWORDS:
            negatives.update(DOMAIN_KEYWORDS[self.domain]['negative'])
        
        # Add specific hard negatives for culinary domain
        if self.domain == 'culinary' and ('vegetarian' in self.query_lower or 'vegan' in self.query_lower):
            negatives.update(DOMAIN_KEYWORDS['culinary']['negative'])
            
        return negatives

    def _get_distractor_titles(self) -> set:
        """Identifies titles that would be irrelevant based on the query."""
        distractors = set()
        if self.domain == 'culinary':
            if 'dinner' in self.query_lower:
                distractors.update(['breakfast', 'lunch'])
            if 'lunch' in self.query_lower:
                distractors.update(['breakfast', 'dinner'])
        return distractors

    def filter_and_rerank(self, sections: list) -> list:
        """
        Applies hard filters and a nuanced scoring model to the list of sections.
        """
        filtered_sections = []
        for section in sections:
            content_lower = section['content'].lower()
            doc_name_lower = section['document'].lower()

            # --- Hard Filter: Check for absolute negative keywords ---
            if any(neg_keyword in content_lower for neg_keyword in self.negative_keywords):
                logging.warning(f"FILTERED (contains negative keyword): Page {section['page_num']} from {section['document']}")
                continue

            # --- Score-based filtering and boosting ---
            score = section.get('similarity_score', 0.5)

            # 1. Penalize sections from documents with distracting titles
            if any(distractor in doc_name_lower for distractor in self.distractor_titles):
                score *= 0.1  # Heavy penalty for wrong document type
                logging.info(f"PENALIZED (distracting title): Page {section['page_num']} from {section['document']}")

            # 2. Boost sections that contain the most important positive keywords
            keyword_hits = sum(1 for keyword in self.positive_keywords if keyword in content_lower)
            
            # Apply a boost proportional to the number of keyword hits
            if keyword_hits > 0:
                boost_factor = 1.0 + (0.2 * keyword_hits) # e.g., 2 hits = 1.4x boost
                score *= boost_factor
            
            section['final_score'] = score
            filtered_sections.append(section)

        # Sort by the new final score
        reranked_sections = sorted(filtered_sections, key=lambda x: x.get('final_score', 0), reverse=True)
        return reranked_sections
