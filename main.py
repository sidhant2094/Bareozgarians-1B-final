import os
import json
import glob
import logging
import re
from datetime import datetime
from pytz import timezone as pytz_timezone
from tqdm import tqdm
from collections import defaultdict

# Import core processing modules from the 'core' directory
from core.pdf_processor import PDFProcessor
from core.ranking import SectionRanker
from core.relevance_filter import RelevanceFilter

# --- Setup robust logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    """
    Main execution function. Processes all PDFs in the input directory,
    aggregates the results, and generates a single consolidated JSON file.
    """
    # Use environment variables for paths, with local defaults for Mac execution.
    input_dir = os.getenv('INPUT_DIR', 'input')
    output_dir = os.getenv('OUTPUT_DIR', 'output')
    
    # Ensure the output directory exists when running locally
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    json_config_path = glob.glob(os.path.join(input_dir, '*.json'))
    if not json_config_path:
        logging.error(f"FATAL: No configuration JSON file found in '{input_dir}'.")
        return
        
    input_path = json_config_path[0]
    logging.info(f"Loading configuration from: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        persona = config['persona']['role']
        job_to_be_done = config['job_to_be_done']['task']
    except Exception as e:
        logging.error(f"FATAL: Could not load persona/job from {input_path}. Error: {e}")
        return

    logging.info("Initializing core components...")
    try:
        pdf_processor = PDFProcessor()
        ranker = SectionRanker()
        query = f"Persona: {persona}. Task: {job_to_be_done}"
        relevance_filter = RelevanceFilter(query)
    except Exception as e:
        logging.error(f"FATAL: Failed to initialize models. Error: {e}")
        return
        
    pdf_files = sorted(glob.glob(os.path.join(input_dir, '*.pdf')))
    if not pdf_files:
        logging.warning("No PDF files found in the input directory.")
        return

    # --- MAJOR CHANGE HERE: Initialize lists to hold all results ---
    all_sections_list = []
    all_subsections_list = []

    logging.info(f"Found {len(pdf_files)} PDF(s) to process.")
    for pdf_path in tqdm(pdf_files, desc="Processing all documents"):
        # 1. Extract sections from the current PDF
        sections = pdf_processor.extract_sections(pdf_path)
        if not sections:
            continue
        
        # 2. Rank and filter sections for this PDF
        semantically_ranked = ranker.rank_sections(query, sections)
        final_ranked = relevance_filter.filter_and_rerank(semantically_ranked)
        
        # 3. Add all processed sections to the master list to be ranked globally later
        all_sections_list.extend(final_ranked)

    # --- NEW LOGIC: Process all collected results together ---
    if not all_sections_list:
        logging.error("No relevant sections found across all documents. No output file will be generated.")
        return

    # 1. Sort the master list of all sections from all documents by their final score
    globally_ranked_sections = sorted(all_sections_list, key=lambda x: x.get('final_score', 0), reverse=True)

    # 2. Prepare the final top 5 sections for output
    final_extracted_sections = []
    seen_titles = set()
    for section in globally_ranked_sections:
        if len(final_extracted_sections) >= 5:
            break
        if section['title'] not in seen_titles:
            final_extracted_sections.append({
                "document": section['document'],
                "section_title": section['title'],
                "page_number": section['page_num']
            })
            seen_titles.add(section['title'])

    # 3. Assign the final importance rank
    for i, sec in enumerate(final_extracted_sections):
        sec["importance_rank"] = i + 1

    # 4. Create the subsection analysis from the globally ranked sections
    # We will check the top 10 globally ranked sections for relevant paragraphs
    for section in globally_ranked_sections[:10]:
        paragraphs = re.split(r'\n{1,}', section['content'])
        for para in paragraphs:
            para = para.strip()
            if len(para.split()) < 8:
                continue
            if any(kw in para.lower() for kw in relevance_filter.positive_keywords):
                all_subsections_list.append({
                    "document": section['document'],
                    "refined_text": para,
                    "page_number": section['page_num']
                })
    
    # --- ASSEMBLE AND WRITE THE SINGLE FINAL JSON ---
    final_output_data = {
        "metadata": {
            "input_documents": [os.path.basename(p) for p in pdf_files],
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.now(pytz_timezone('UTC')).isoformat()
        },
        "extracted_sections": final_extracted_sections,
        "subsection_analysis": all_subsections_list
    }

    output_path = os.path.join(output_dir, "output.json")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Successfully generated consolidated output at {output_path}")
    except IOError as e:
        logging.error(f"Could not write final output file {output_path}. Error: {e}")


if __name__ == '__main__':
    main()