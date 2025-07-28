import fitz  # PyMuPDF
import os
import logging
from collections import Counter
import re

class PDFProcessor:
    """
    Handles the extraction of structured sections (title + content) from PDF files
    by intelligently detecting headers based on font styling.
    """
    def __init__(self):
        logging.info("PDFProcessor initialized for high-accuracy header extraction.")

    def extract_sections(self, pdf_path: str) -> list:
        """
        Extracts structured sections from a PDF. A section consists of a
        header and all the content that follows it until the next header.

        Args:
            pdf_path (str): The full path to the PDF file.

        Returns:
            list: A list of section dictionaries, each with a 'title' and 'content'.
        """
        doc_name = os.path.basename(pdf_path)
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logging.error(f"Failed to open {doc_name}: {e}")
            return []

        sections = []
        # Process page by page to maintain context
        for page_num, page in enumerate(doc, start=1):
            blocks = page.get_text("dict").get("blocks", [])
            if not blocks:
                continue

            # 1. Identify the most common font size to determine body text style
            font_sizes = [s['size'] for b in blocks if b['type'] == 0 for l in b['lines'] for s in l['spans']]
            if not font_sizes:
                continue
            
            size_counts = Counter(round(s, 2) for s in font_sizes)
            body_size = size_counts.most_common(1)[0][0] if size_counts else 12.0

            # 2. Iterate through blocks to group content under headers
            current_header = f"Content from Page {page_num}" # Default title
            current_content_blocks = []

            for b in blocks:
                if b['type'] != 0 or not b.get('lines'): continue
                
                first_line = b['lines'][0]
                first_span = first_line['spans'][0]
                text = " ".join(s['text'] for s in first_line['spans']).strip()

                # A more robust header detection heuristic
                is_header = (
                    round(first_span['size'], 2) > body_size * 1.1 and
                    ('bold' in first_span['font'].lower() or 'black' in first_span['font'].lower()) and
                    len(text.split()) < 12 and
                    len(text) > 3 and
                    not text.endswith('.') and
                    text[0].isupper()
                )

                if is_header:
                    # If we have content for the previous header, save it as a section
                    if current_content_blocks:
                        full_content = "\n".join(current_content_blocks).strip()
                        if len(full_content.split()) > 10: # Only save substantial sections
                            sections.append({
                                'document': doc_name,
                                'page_num': page_num,
                                'title': current_header,
                                'content': full_content
                            })
                    
                    # Start a new section with the detected header
                    current_header = text
                    # --- FIX IS HERE ---
                    # The rest of the lines from the header block are added as content.
                    # The original code used an undefined variable 'l'. This now correctly
                    # processes the remaining lines in the current block 'b'.
                    if len(b['lines']) > 1:
                        remaining_content = " ".join("".join(s['text'] for s in line['spans']) for line in b['lines'][1:])
                        current_content_blocks = [remaining_content]
                    else:
                        current_content_blocks = []
                else:
                    # This block is content, add all its lines to the current section
                    block_text = " ".join("".join(s['text'] for s in l['spans']) for l in b['lines'])
                    current_content_blocks.append(block_text)
            
            # Add the last section from the page to the list
            if current_content_blocks:
                full_content = "\n".join(current_content_blocks).strip()
                if len(full_content.split()) > 10:
                    sections.append({
                        'document': doc_name,
                        'page_num': page_num,
                        'title': current_header,
                        'content': full_content
                    })

        doc.close()
        logging.info(f"Extracted {len(sections)} structured sections from {doc_name}.")
        return sections