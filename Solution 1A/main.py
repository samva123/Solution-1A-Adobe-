# import fitz  # PyMuPDF
# import json
# import re
# import os
# from typing import List, Dict, Any
# from dataclasses import dataclass
# import logging
# from pathlib import Path

# @dataclass
# class HeadingCandidate:
#     text: str
#     page: int
#     font_size: float
#     font_name: str
#     is_bold: bool
#     y_position: float
#     x_position: float
#     bbox: tuple

# class PDFOutlineExtractor:
#     def __init__(self):
#         self.setup_logging()
#         # Common patterns for headings
#         self.heading_patterns = [
#             r'^\d+\.\s+',  # 1. Introduction
#             r'^\d+\.\d+\s+',  # 1.1 Overview
#             r'^\d+\.\d+\.\d+\s+',  # 1.1.1 Details
#             r'^Chapter\s+\d+',  # Chapter 1
#             r'^Section\s+\d+',  # Section 1
#             r'^[A-Z][A-Z\s]{2,}$',  # ALL CAPS
#             r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$'  # Title Case
#         ]
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         for span in line["spans"]:
#                             text = span["text"].strip()
#                             if text and len(text) > 2:
#                                 candidate = HeadingCandidate(
#                                     text=text,
#                                     page=page_num + 1,
#                                     font_size=span["size"],
#                                     font_name=span["font"],
#                                     is_bold="Bold" in span["font"] or span["flags"] & 2**4,
#                                     y_position=span["bbox"][1],
#                                     x_position=span["bbox"][0],
#                                     bbox=span["bbox"]
#                                 )
#                                 candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def extract_title(self, candidates: List[HeadingCandidate]) -> str:
#         """Extract document title using heuristics"""
#         # Look for title in first few pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Sort by font size (largest first) and position (topmost first)
#         sorted_candidates = sorted(
#             first_page_candidates,
#             key=lambda x: (-x.font_size, x.y_position)
#         )
        
#         # Title is likely to be:
#         # 1. Large font size
#         # 2. At the top of early pages
#         # 3. Not too long
#         # 4. Not a common heading pattern
        
#         for candidate in sorted_candidates[:10]:  # Check top 10 candidates
#             text = candidate.text.strip()
            
#             # Skip if too long or too short
#             if len(text) < 5 or len(text) > 100:
#                 continue
                
#             # Skip if matches common heading patterns
#             if any(re.match(pattern, text) for pattern in self.heading_patterns):
#                 continue
                
#             # Skip if all caps and very short (likely headers/footers)
#             if text.isupper() and len(text) < 15:
#                 continue
                
#             return text
        
#         # Fallback to first reasonable candidate
#         return sorted_candidates[0].text if sorted_candidates else "Untitled Document"
    
#     def classify_heading_level(self, candidate: HeadingCandidate, avg_font_size: float) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
        
#         # Pattern-based classification
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / avg_font_size
        
#         if size_ratio > 1.5:
#             return "H1"
#         elif size_ratio > 1.2:
#             return "H2"
#         elif size_ratio > 1.0:
#             return "H3"
        
#         # Bold text slightly above average
#         if candidate.is_bold and size_ratio > 0.9:
#             return "H2"
        
#         return "H3"  # Default
    
#     def is_likely_heading(self, candidate: HeadingCandidate, avg_font_size: float) -> bool:
#         """Determine if a text candidate is likely a heading"""
#         text = candidate.text.strip()
        
#         # Skip very short or very long text
#         if len(text) < 3 or len(text) > 200:
#             return False
        
#         # Skip if contains too many numbers (likely content)
#         if len(re.findall(r'\d', text)) > len(text) * 0.5:
#             return False
        
#         # Check for heading patterns
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 return True
        
#         # Check font size (should be larger than average)
#         if candidate.font_size > avg_font_size * 1.1:
#             return True
        
#         # Check if bold and reasonable size
#         if candidate.is_bold and candidate.font_size >= avg_font_size * 0.9:
#             return True
        
#         # Check if all caps (but not too long)
#         if text.isupper() and 5 < len(text) < 50:
#             return True
        
#         return False
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Calculate average font size for reference
#         avg_font_size = sum(c.font_size for c in candidates) / len(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates)
        
#         # Filter heading candidates
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, avg_font_size)
#         ]
        
#         # Remove duplicates and sort
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             text_key = f"{candidate.text.strip()}_{candidate.page}"
#             if text_key not in seen_texts:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Build outline
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, avg_font_size)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main()

























































# import fitz  # PyMuPDF
# import json
# import re
# import os
# from typing import List, Dict, Any
# from dataclasses import dataclass
# import logging
# from pathlib import Path
# from collections import Counter

# @dataclass
# class HeadingCandidate:
#     text: str
#     page: int
#     font_size: float
#     font_name: str
#     is_bold: bool
#     y_position: float
#     x_position: float
#     bbox: tuple

# class PDFOutlineExtractor:
#     def __init__(self):
#         self.setup_logging()
#         # More specific patterns for headings
#         self.heading_patterns = [
#             r'^\d+\.\s+[A-Z]',  # 1. Introduction (must start with capital)
#             r'^\d+\.\d+\s+[A-Z]',  # 1.1 Overview
#             r'^\d+\.\d+\.\d+\s+[A-Z]',  # 1.1.1 Details
#             r'^Chapter\s+\d+',  # Chapter 1
#             r'^Section\s+\d+',  # Section 1
#             r'^[A-Z][A-Z\s]{4,}$',  # ALL CAPS (minimum 5 chars)
#             r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,5}$'  # Title Case (max 6 words)
#         ]
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns
#         if any(text.lower().startswith(prefix) for prefix in [
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are'
#         ]):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (but not if too long)
#         if text.isupper() and 3 < len(text) < 30:
#             score += 2
        
#         # Title case bonus
#         if text.istitle() and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main()




















































# import fitz  # PyMuPDF
# import json
# import re
# import os
# from typing import List, Dict, Any
# from dataclasses import dataclass
# import logging
# from pathlib import Path
# from collections import Counter

# @dataclass
# class HeadingCandidate:
#     text: str
#     page: int
#     font_size: float
#     font_name: str
#     is_bold: bool
#     y_position: float
#     x_position: float
#     bbox: tuple

# class PDFOutlineExtractor:
#     def __init__(self):
#         self.setup_logging()
#         # Multilingual patterns for headings
#         self.heading_patterns = [
#             # Numbered patterns (universal)
#             r'^\d+\.\s+',  # 1. Introduction
#             r'^\d+\.\d+\s+',  # 1.1 Overview  
#             r'^\d+\.\d+\.\d+\s+',  # 1.1.1 Details
#             r'^\d+\s+',  # 1 Introduction (no dot)
#             r'^\(\d+\)\s+',  # (1) Introduction
#             r'^[IVXLCDM]+\.\s+',  # Roman numerals: I. II. III.
            
#             # English patterns
#             r'^Chapter\s+\d+',  # Chapter 1
#             r'^Section\s+\d+',  # Section 1
#             r'^CHAPTER\s+\d+',  # CHAPTER 1
            
#             # Japanese patterns
#             r'^第\d+章',  # 第1章 (Chapter 1)
#             r'^第\d+節',  # 第1節 (Section 1)
#             r'^\d+章',   # 1章
#             r'^\d+\.?\s*[はがをに]',  # Japanese particles after numbers
            
#             # General Unicode patterns
#             r'^[\u4e00-\u9fff]+
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns (multilingual)
#         exclude_patterns = [
#             # English
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are',
#             # Japanese  
#             'ページ', '図', '表', '参照', '例えば', 'として',
#             # Common punctuation that indicates content
#             '。', '、', '.', ',', ';', ':', '!', '?'
#         ]
        
#         text_lower = text.lower()
#         if any(text_lower.startswith(prefix.lower()) for prefix in exclude_patterns):
#             return False
            
#         # Exclude if ends with sentence punctuation (likely content)
#         if text.endswith(('。', '.', '!', '?', ',', ';')):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (multilingual)
#         if self.is_all_caps_multilingual(text) and 3 < len(text) < 30:
#             score += 2
            
#         # Title case bonus (basic check)
#         if self.is_title_case_multilingual(text) and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def is_all_caps_multilingual(self, text: str) -> bool:
#         """Check if text is all caps across different languages"""
#         # For languages without case distinction, check if it's short and standalone
#         if not any(c.isalpha() for c in text):
#             return False
            
#         # Check if all alphabetic characters are uppercase
#         alpha_chars = [c for c in text if c.isalpha()]
#         if not alpha_chars:
#             return False
            
#         return all(c.isupper() for c in alpha_chars)
    
#     def is_title_case_multilingual(self, text: str) -> bool:
#         """Basic title case check that works across languages"""
#         words = text.split()
#         if not words:
#             return False
            
#         # Check if first character of each word is uppercase (where applicable)
#         for word in words:
#             if word and word[0].isalpha() and not word[0].isupper():
#                 return False
#         return True
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main(),  # Chinese/Japanese characters only
#             r'^[\u3040-\u309f\u30a0-\u30ff]+
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns
#         if any(text.lower().startswith(prefix) for prefix in [
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are'
#         ]):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (but not if too long)
#         if text.isupper() and 3 < len(text) < 30:
#             score += 2
        
#         # Title case bonus
#         if text.istitle() and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main(),  # Hiragana/Katakana only
#             r'^[А-ЯЁ][А-ЯЁ\s]{4,}
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns
#         if any(text.lower().startswith(prefix) for prefix in [
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are'
#         ]):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (but not if too long)
#         if text.isupper() and 3 < len(text) < 30:
#             score += 2
        
#         # Title case bonus
#         if text.istitle() and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main(),  # Cyrillic ALL CAPS
#             r'^[A-Z\u00C0-\u00D6\u00D8-\u00DE][A-Z\u00C0-\u00D6\u00D8-\u00DE\s]{4,}
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns
#         if any(text.lower().startswith(prefix) for prefix in [
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are'
#         ]):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (but not if too long)
#         if text.isupper() and 3 < len(text) < 30:
#             score += 2
        
#         # Title case bonus
#         if text.istitle() and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main(),  # Extended Latin ALL CAPS
            
#             # Title case patterns (multilingual)
#             r'^[\p{Lu}][\p{L}\s]{2,50}
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns
#         if any(text.lower().startswith(prefix) for prefix in [
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are'
#         ]):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (but not if too long)
#         if text.isupper() and 3 < len(text) < 30:
#             score += 2
        
#         # Title case bonus
#         if text.istitle() and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main(),  # Unicode title case (if regex supports \p)
#         ]
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns
#         if any(text.lower().startswith(prefix) for prefix in [
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are'
#         ]):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (but not if too long)
#         if text.isupper() and 3 < len(text) < 30:
#             score += 2
        
#         # Title case bonus
#         if text.istitle() and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main()
















































































# import fitz  # PyMuPDF
# import json
# import re
# import os
# from typing import List, Dict, Any
# from dataclasses import dataclass
# import logging
# from pathlib import Path
# from collections import Counter

# @dataclass
# class HeadingCandidate:
#     text: str
#     page: int
#     font_size: float
#     font_name: str
#     is_bold: bool
#     y_position: float
#     x_position: float
#     bbox: tuple

# class PDFOutlineExtractor:
#     def __init__(self):
#         self.setup_logging()
#         # Multilingual patterns for headings
#         self.heading_patterns = [
#             # Numbered patterns (universal)
#             r'^\d+\.\s+',  # 1. Introduction
#             r'^\d+\.\d+\s+',  # 1.1 Overview  
#             r'^\d+\.\d+\.\d+\s+',  # 1.1.1 Details
#             r'^\d+\s+',  # 1 Introduction (no dot)
#             r'^\(\d+\)\s+',  # (1) Introduction
#             r'^[IVXLCDM]+\.\s+',  # Roman numerals: I. II. III.
            
#             # English patterns
#             r'^Chapter\s+\d+',  # Chapter 1
#             r'^Section\s+\d+',  # Section 1
#             r'^CHAPTER\s+\d+',  # CHAPTER 1
            
#             # Japanese patterns
#             r'^第\d+章',  # 第1章 (Chapter 1)
#             r'^第\d+節',  # 第1節 (Section 1)
#             r'^\d+章',   # 1章
#             r'^\d+\.?\s*[はがをに]',  # Japanese particles after numbers
            
#             # General Unicode patterns
#             r'^[\u4e00-\u9fff]+$',  # Chinese/Japanese characters only
#             r'^[\u3040-\u309f\u30a0-\u30ff]+$',  # Hiragana/Katakana only
#             r'^[А-ЯЁ][А-ЯЁ\s]{4,}$',  # Cyrillic ALL CAPS
#             r'^[A-Z\u00C0-\u00D6\u00D8-\u00DE][A-Z\u00C0-\u00D6\u00D8-\u00DE\s]{4,}$'  # Extended Latin ALL CAPS
#         ]
        
#     def setup_logging(self):
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
    
#     def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
#         """Extract text with formatting information from PDF"""
#         doc = fitz.open(pdf_path)
#         candidates = []
        
#         for page_num in range(len(doc)):
#             page = doc.load_page(page_num)
#             blocks = page.get_text("dict")
            
#             for block in blocks["blocks"]:
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         # Combine spans in the same line to handle split headings
#                         line_text = ""
#                         line_font_info = None
                        
#                         for span in line["spans"]:
#                             line_text += span["text"]
#                             if line_font_info is None:
#                                 line_font_info = span
                        
#                         text = line_text.strip()
#                         if text and len(text) > 2 and line_font_info:
#                             candidate = HeadingCandidate(
#                                 text=text,
#                                 page=page_num + 1,
#                                 font_size=line_font_info["size"],
#                                 font_name=line_font_info["font"],
#                                 is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
#                                 y_position=line_font_info["bbox"][1],
#                                 x_position=line_font_info["bbox"][0],
#                                 bbox=line_font_info["bbox"]
#                             )
#                             candidates.append(candidate)
        
#         doc.close()
#         return candidates
    
#     def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
#         """Analyze font usage patterns in the document"""
#         font_sizes = [c.font_size for c in candidates]
#         font_counter = Counter(font_sizes)
        
#         # Find the most common font size (likely body text)
#         most_common_size = font_counter.most_common(1)[0][0]
        
#         # Calculate statistics
#         unique_sizes = sorted(set(font_sizes), reverse=True)
        
#         return {
#             'body_text_size': most_common_size,
#             'avg_size': sum(font_sizes) / len(font_sizes),
#             'unique_sizes': unique_sizes,
#             'size_distribution': font_counter
#         }
    
#     def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
#         """Extract document title using improved heuristics"""
#         # Look for title in first 3 pages
#         first_page_candidates = [c for c in candidates if c.page <= 3]
        
#         if not first_page_candidates:
#             return "Untitled Document"
        
#         # Filter potential titles
#         potential_titles = []
#         body_size = font_stats['body_text_size']
        
#         for candidate in first_page_candidates:
#             text = candidate.text.strip()
            
#             # Title criteria
#             if (5 <= len(text) <= 100 and  # Reasonable length
#                 candidate.font_size > body_size * 1.2 and  # Larger than body
#                 not any(re.match(pattern, text) for pattern in self.heading_patterns) and  # Not a numbered heading
#                 not text.lower().startswith(('page ', 'figure ', 'table ')) and  # Not page/figure reference
#                 len(text.split()) <= 10):  # Not too many words
                
#                 potential_titles.append((candidate, candidate.font_size))
        
#         if potential_titles:
#             # Sort by font size (largest first)
#             potential_titles.sort(key=lambda x: x[1], reverse=True)
#             return potential_titles[0][0].text
        
#         # Fallback
#         return first_page_candidates[0].text if first_page_candidates else "Untitled Document"
    
#     def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
#         """Determine if a text candidate is likely a heading with stricter criteria"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Exclude very short, very long, or content-heavy text
#         if len(text) < 3 or len(text) > 150:
#             return False
        
#         # Exclude if too many numbers (likely content, not heading)
#         digit_ratio = len(re.findall(r'\d', text)) / len(text)
#         if digit_ratio > 0.3:
#             return False
        
#         # Exclude common non-heading patterns (multilingual)
#         exclude_patterns = [
#             # English
#             'page ', 'figure ', 'table ', 'see ', 'as shown', 'for example',
#             'in this', 'this is', 'we can', 'it is', 'there are',
#             # Japanese  
#             'ページ', '図', '表', '参照', '例えば', 'として'
#         ]
        
#         text_lower = text.lower()
#         if any(text_lower.startswith(prefix.lower()) for prefix in exclude_patterns):
#             return False
            
#         # Exclude if ends with sentence punctuation (likely content)
#         if text.endswith(('。', '.', '!', '?', ',', ';')):
#             return False
        
#         # Exclude if contains too many common words (likely paragraph text)
#         common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
#         word_count = len(text.split())
#         common_word_count = sum(1 for word in text.lower().split() if word in common_words)
#         if word_count > 3 and common_word_count / word_count > 0.4:
#             return False
        
#         # Positive indicators for headings
#         score = 0
        
#         # Pattern match bonus
#         for pattern in self.heading_patterns:
#             if re.match(pattern, text):
#                 score += 3
#                 break
        
#         # Font size bonus
#         size_ratio = candidate.font_size / body_size
#         if size_ratio > 1.5:
#             score += 3
#         elif size_ratio > 1.2:
#             score += 2
#         elif size_ratio > 1.05:
#             score += 1
        
#         # Bold bonus
#         if candidate.is_bold:
#             score += 1
        
#         # Position bonus (left-aligned, standalone)
#         if candidate.x_position < 100:  # Left margin
#             score += 1
        
#         # All caps bonus (multilingual)
#         if self.is_all_caps_multilingual(text) and 3 < len(text) < 30:
#             score += 2
            
#         # Title case bonus (basic check)
#         if self.is_title_case_multilingual(text) and word_count <= 8:
#             score += 1
        
#         # Need at least score of 2 to be considered a heading
#         return score >= 2
    
#     def is_all_caps_multilingual(self, text: str) -> bool:
#         """Check if text is all caps across different languages"""
#         # For languages without case distinction, check if it's short and standalone
#         if not any(c.isalpha() for c in text):
#             return False
            
#         # Check if all alphabetic characters are uppercase
#         alpha_chars = [c for c in text if c.isalpha()]
#         if not alpha_chars:
#             return False
            
#         return all(c.isupper() for c in alpha_chars)
    
#     def is_title_case_multilingual(self, text: str) -> bool:
#         """Basic title case check that works across languages"""
#         words = text.split()
#         if not words:
#             return False
            
#         # Check if first character of each word is uppercase (where applicable)
#         for word in words:
#             if word and word[0].isalpha() and not word[0].isupper():
#                 return False
#         return True
    
#     def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
#         """Classify heading level based on multiple factors"""
#         text = candidate.text.strip()
#         body_size = font_stats['body_text_size']
        
#         # Pattern-based classification (highest priority)
#         if re.match(r'^\d+\.\s+', text):
#             return "H1"
#         elif re.match(r'^\d+\.\d+\s+', text):
#             return "H2"
#         elif re.match(r'^\d+\.\d+\.\d+\s+', text):
#             return "H3"
        
#         # Font size based classification
#         size_ratio = candidate.font_size / body_size
        
#         # Determine heading levels based on font size distribution
#         heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        
#         if len(heading_sizes) >= 3:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             elif candidate.font_size >= heading_sizes[1]:
#                 return "H2"
#             else:
#                 return "H3"
#         elif len(heading_sizes) == 2:
#             if candidate.font_size >= heading_sizes[0]:
#                 return "H1"
#             else:
#                 return "H2"
#         else:
#             # Fallback to size ratio
#             if size_ratio > 1.4:
#                 return "H1"
#             elif size_ratio > 1.1:
#                 return "H2"
#             else:
#                 return "H3"
    
#     def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
#         """Extract structured outline from PDF"""
#         self.logger.info(f"Processing PDF: {pdf_path}")
        
#         # Extract all text with formatting
#         candidates = self.extract_text_with_formatting(pdf_path)
        
#         if not candidates:
#             return {"title": "Empty Document", "outline": []}
        
#         # Analyze font statistics
#         font_stats = self.get_font_statistics(candidates)
        
#         # Extract title
#         title = self.extract_title(candidates, font_stats)
        
#         # Filter heading candidates with stricter criteria
#         heading_candidates = [
#             c for c in candidates 
#             if self.is_likely_heading(c, font_stats)
#         ]
        
#         self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        
#         # Remove duplicates (same text on same page)
#         seen_texts = set()
#         unique_headings = []
        
#         for candidate in heading_candidates:
#             # Create a more specific key to avoid false duplicates
#             text_normalized = re.sub(r'\s+', ' ', candidate.text.strip().lower())
#             text_key = f"{text_normalized}_{candidate.page}"
            
#             if text_key not in seen_texts and len(candidate.text.strip()) > 0:
#                 seen_texts.add(text_key)
#                 unique_headings.append(candidate)
        
#         # Sort by page and position
#         unique_headings.sort(key=lambda x: (x.page, x.y_position))
        
#         # Classify heading levels
#         outline = []
#         for candidate in unique_headings:
#             level = self.classify_heading_level(candidate, font_stats, unique_headings)
#             outline.append({
#                 "level": level,
#                 "text": candidate.text.strip(),
#                 "page": candidate.page
#             })
        
#         self.logger.info(f"Final outline contains {len(outline)} headings")
        
#         return {
#             "title": title,
#             "outline": outline
#         }
    
#     def process_directory(self, input_dir: str, output_dir: str):
#         """Process all PDFs in input directory"""
#         input_path = Path(input_dir)
#         output_path = Path(output_dir)
#         output_path.mkdir(exist_ok=True)
        
#         pdf_files = list(input_path.glob("*.pdf"))
#         self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
#         for pdf_file in pdf_files:
#             try:
#                 self.logger.info(f"Processing {pdf_file.name}")
                
#                 # Extract outline
#                 outline = self.extract_outline(str(pdf_file))
                
#                 # Save output
#                 output_file = output_path / f"{pdf_file.stem}.json"
#                 with open(output_file, 'w', encoding='utf-8') as f:
#                     json.dump(outline, f, indent=2, ensure_ascii=False)
                
#                 self.logger.info(f"Saved outline to {output_file}")
                
#             except Exception as e:
#                 self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

# def main():
#     """Main execution function"""
#     extractor = PDFOutlineExtractor()
    
#     # Use the expected directory structure
#     input_dir = "/app/input"
#     output_dir = "/app/output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     # Process all PDFs
#     extractor.process_directory(input_dir, output_dir)

# if __name__ == "__main__":
#     main()


































import fitz  # PyMuPDF
import json
import re
import os
import unicodedata
from typing import List, Dict, Any
from dataclasses import dataclass
import logging
from pathlib import Path
from collections import Counter

@dataclass
class HeadingCandidate:
    text: str
    page: int
    font_size: float
    font_name: str
    is_bold: bool
    y_position: float
    x_position: float
    bbox: tuple

class PDFOutlineExtractor:
    def __init__(self):
        self.setup_logging()
        self.heading_patterns = [
            r'^\d+\.\s+', r'^\d+\.\d+\s+', r'^\d+\.\d+\.\d+\s+', r'^\d+\s+',
            r'^\(\d+\)\s+', r'^[IVXLCDM]+\.\s+', r'^Chapter\s+\d+', r'^Section\s+\d+',
            r'^CHAPTER\s+\d+', r'^Part\s+\d+', r'^PART\s+\d+', r'^अध्याय\s*[१२३४५६७८९०\d]+',
            r'^भाग\s*[१२३४५६७८९०\d]+', r'^खंड\s*[१२३४५६७८९०\d]+', r'^परिच्छेद\s*[१२३४५६७८९०\d]+',
            r'^प्रकरण\s*[१२३४५६७८९०\d]+', r'^धारा\s*[१२३४५६७८९०\d]+', r'^उप-धारा\s*[१२३४५६७८९०\d]+',
            r'^अनुभाग\s*[१२३४५६७८९०\d]+', r'^विषय\s*[१२३४५६७८९०\d]+', r'^[१२३४५६७८९०]+\.\s*',
            r'^[१२३४५६७८९०]+\s+', r'^\([१२३४५६७८९०]+\)\s*', r'^\d+\.\s*[का|की|के|में|से|पर|द्वारा]',
            r'^[१२३४५६७८९०]+\.\s*[का|की|के|में|से|पर|द्वारा]', r'^प्रश्न\s*[१२३४५६७८९०\d]*:?',
            r'^उत्तर\s*[१२३४५६७८९०\d]*:?', r'^समस्या\s*[१२३४५६७८९०\d]*:?', r'^उदाहरण\s*[१२३४५६७८९०\d]*:?',
            r'^第\d+章', r'^第\d+節', r'^\d+章', r'^\d+\.?\s*[はがをに]', r'^[\u4e00-\u9fff]+$',
            r'^[\u3040-\u309f\u30a0-\u30ff]+$', r'^[\u0900-\u097F]+$', r'^[А-ЯЁ][А-ЯЁ\s]{4,}$',
            r'^[A-Z\u00C0-\u00D6\u00D8-\u00DE][A-Z\u00C0-\u00D6\u00D8-\u00DE\s]{4,}$'
        ]
        self.hindi_to_english_digits = {
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
        }

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def normalize_hindi_text(self, text: str) -> str:
        for hindi_digit, english_digit in self.hindi_to_english_digits.items():
            text = text.replace(hindi_digit, english_digit)
        return text

    def contains_devanagari(self, text: str) -> bool:
        return any('\u0900' <= ch <= '\u097F' for ch in text)

    def extract_text_with_formatting(self, pdf_path: str) -> List[HeadingCandidate]:
        doc = fitz.open(pdf_path)
        candidates = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        line_font_info = None
                        for span in line["spans"]:
                            line_text += span["text"]
                            if line_font_info is None:
                                line_font_info = span
                        text = line_text.strip()
                        if text and len(text) > 1 and line_font_info:
                            candidate = HeadingCandidate(
                                text=text,
                                page=page_num + 1,
                                font_size=line_font_info["size"],
                                font_name=line_font_info["font"],
                                is_bold="Bold" in line_font_info["font"] or line_font_info["flags"] & 2**4,
                                y_position=line_font_info["bbox"][1],
                                x_position=line_font_info["bbox"][0],
                                bbox=line_font_info["bbox"]
                            )
                            candidates.append(candidate)
        doc.close()
        return candidates

    def get_font_statistics(self, candidates: List[HeadingCandidate]) -> Dict:
        font_sizes = [c.font_size for c in candidates]
        font_counter = Counter(font_sizes)
        most_common_size = font_counter.most_common(1)[0][0]
        unique_sizes = sorted(set(font_sizes), reverse=True)
        return {
            'body_text_size': most_common_size,
            'avg_size': sum(font_sizes) / len(font_sizes),
            'unique_sizes': unique_sizes,
            'size_distribution': font_counter
        }

    def extract_title(self, candidates: List[HeadingCandidate], font_stats: Dict) -> str:
        first_page_candidates = [c for c in candidates if c.page <= 3]
        if not first_page_candidates:
            return "शीर्षकहीन दस्तावेज़" if self.has_hindi_content(candidates) else "Untitled Document"
        potential_titles = []
        body_size = font_stats['body_text_size']
        for candidate in first_page_candidates:
            text = candidate.text.strip()
            normalized_text = self.normalize_hindi_text(text)
            if (2 <= len(text) <= 120 and
                candidate.font_size > body_size * 1.1 and
                not any(re.match(pattern, normalized_text) for pattern in self.heading_patterns) and
                not self.is_common_non_title_text(text.lower()) and
                len(text.split()) <= 15):
                potential_titles.append((candidate, candidate.font_size))
        if potential_titles:
            potential_titles.sort(key=lambda x: x[1], reverse=True)
            return potential_titles[0][0].text
        return first_page_candidates[0].text if first_page_candidates else (
            "शीर्षकहीन दस्तावेज़" if self.has_hindi_content(candidates) else "Untitled Document"
        )

    def has_hindi_content(self, candidates: List[HeadingCandidate]) -> bool:
        return any(self.contains_devanagari(c.text) for c in candidates[:50])

    def is_common_non_title_text(self, text_lower: str) -> bool:
        english = ['page ', 'figure ', 'table ', 'see ', 'as shown', 'for example', 'in this', 'this is', 'we can', 'it is', 'there are']
        hindi = ['पृष्ठ ', 'चित्र ', 'तालिका ', 'देखें ', 'जैसा कि दिखाया', 'उदाहरण के लिए', 'इसमें ', 'यह है', 'हम कर सकते', 'यह है']
        return any(text_lower.startswith(p.lower()) for p in english + hindi)

    def is_likely_heading(self, candidate: HeadingCandidate, font_stats: Dict) -> bool:
        text = candidate.text.strip()
        normalized_text = self.normalize_hindi_text(text)
        body_size = font_stats['body_text_size']
        if len(text) < 2 or len(text) > 200:
            return False
        digit_ratio = len(re.findall(r'[\d१२३४५६७८९०]', text)) / len(text)
        if digit_ratio > 0.4:
            return False
        if self.is_common_non_title_text(text.lower()):
            return False
        if text.endswith(('।', '।।', '.', '!', '?', ',', ';', '|')):
            return False
        english_common = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        hindi_common = ['और', 'या', 'लेकिन', 'में', 'पर', 'को', 'के', 'से', 'का', 'की', 'है', 'हैं']
        words = text.split()
        if len(words) > 3:
            common_count = sum(1 for word in words if word.lower() in english_common + hindi_common)
            if common_count / len(words) > 0.4:
                return False
        score = 0
        for i, pattern in enumerate(self.heading_patterns):
            if re.match(pattern, normalized_text):
                score += 4 if 6 <= i <= 20 else 3
                break
        size_ratio = candidate.font_size / body_size
        if size_ratio > 1.5: score += 3
        elif size_ratio > 1.2: score += 2
        elif size_ratio > 1.05: score += 1
        if candidate.is_bold: score += 1
        if candidate.x_position < 150: score += 1
        if self.is_all_caps_multilingual(text) and 2 < len(text) < 40: score += 2
        if self.is_title_case_multilingual(text) and len(words) <= 10: score += 1
        if self.contains_devanagari(text): score += 1  # ✅ New Hindi-specific bonus
        return score >= 2

    def is_all_caps_multilingual(self, text: str) -> bool:
        if self.contains_devanagari(text):
            return len(text.split()) <= 6 and not text.endswith(('।', '।।'))
        alpha_chars = [c for c in text if c.isalpha()]
        return all(c.isupper() for c in alpha_chars) if alpha_chars else False

    def is_title_case_multilingual(self, text: str) -> bool:
        words = text.split()
        if not words:
            return False
        if self.contains_devanagari(text):
            return len(words) <= 8
        return all(word[0].isupper() for word in words if word and word[0].isalpha())

    def classify_heading_level(self, candidate: HeadingCandidate, font_stats: Dict, all_headings: List) -> str:
        text = candidate.text.strip()
        normalized_text = self.normalize_hindi_text(text)
        body_size = font_stats['body_text_size']
        h1 = [r'^\d+\.\s+', r'^अध्याय\s*\d+', r'^भाग\s*\d+', r'^[१२३४५६७८९०]+\.\s*', r'^Chapter\s+\d+', r'^CHAPTER\s+\d+']
        h2 = [r'^\d+\.\d+\s+', r'^खंड\s*\d+', r'^परिच्छेद\s*\d+', r'^धारा\s*\d+', r'^Section\s+\d+', r'^\([१२३४५६७८९०\d]+\)\s*']
        h3 = [r'^\d+\.\d+\.\d+\s+', r'^उप-धारा\s*\d+', r'^अनुभाग\s*\d+', r'^प्रकरण\s*\d+', r'^प्रश्न\s*\d*:?', r'^उत्तर\s*\d*:?']
        for pattern in h1:
            if re.match(pattern, normalized_text): return "H1"
        for pattern in h2:
            if re.match(pattern, normalized_text): return "H2"
        for pattern in h3:
            if re.match(pattern, normalized_text): return "H3"
        heading_sizes = sorted(set(h.font_size for h in all_headings), reverse=True)
        if len(heading_sizes) >= 3:
            if candidate.font_size >= heading_sizes[0]: return "H1"
            elif candidate.font_size >= heading_sizes[1]: return "H2"
            else: return "H3"
        elif len(heading_sizes) == 2:
            if candidate.font_size >= heading_sizes[0]: return "H1"
            else: return "H2"
        else:
            if candidate.font_size / body_size > 1.4: return "H1"
            elif candidate.font_size / body_size > 1.1: return "H2"
            else: return "H3"

    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        self.logger.info(f"Processing PDF: {pdf_path}")
        candidates = self.extract_text_with_formatting(pdf_path)
        if not candidates:
            return {"title": "खाली दस्तावेज़", "outline": []}
        font_stats = self.get_font_statistics(candidates)
        title = self.extract_title(candidates, font_stats)
        heading_candidates = [c for c in candidates if self.is_likely_heading(c, font_stats)]
        self.logger.info(f"Found {len(heading_candidates)} potential headings out of {len(candidates)} text elements")
        seen_texts = set()
        unique_headings = []
        for candidate in heading_candidates:
            text_normalized = unicodedata.normalize("NFC", candidate.text.strip())
            text_normalized = re.sub(r'\s+', ' ', self.normalize_hindi_text(text_normalized))
            text_key = f"{text_normalized}_{candidate.page}"
            if text_key not in seen_texts and len(candidate.text.strip()) > 0:
                seen_texts.add(text_key)
                unique_headings.append(candidate)
        unique_headings.sort(key=lambda x: (x.page, x.y_position))
        outline = []
        for candidate in unique_headings:
            level = self.classify_heading_level(candidate, font_stats, unique_headings)
            outline.append({
                "level": level,
                "text": candidate.text.strip(),
                "page": candidate.page
            })
        self.logger.info(f"Final outline contains {len(outline)} headings")
        return {
            "title": title,
            "outline": outline,
            
        }

    def process_directory(self, input_dir: str, output_dir: str):
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        pdf_files = list(input_path.glob("*.pdf"))
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        for pdf_file in pdf_files:
            try:
                self.logger.info(f"Processing {pdf_file.name}")
                outline = self.extract_outline(str(pdf_file))
                output_file = output_path / f"{pdf_file.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(outline, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Saved outline to {output_file}")
            except Exception as e:
                self.logger.error(f"Error processing {pdf_file.name}: {str(e)}")

def main():
    extractor = PDFOutlineExtractor()
    input_dir = "/app/input"
    output_dir = "/app/output"
    os.makedirs(output_dir, exist_ok=True)
    extractor.process_directory(input_dir, output_dir)

if __name__ == "__main__":
    main()
