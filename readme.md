# PDF Structure Extractor

A robust solution for extracting document structure (title and headings) from PDF files, designed for the Connecting the Dots Through Docs hackathon challenge.

## Approach

This solution uses a multi-faceted approach to identify document structure:

### 1. Text Extraction with Formatting
- Uses PyMuPDF (fitz) to extract text with detailed formatting information
- Captures font size, font flags (bold/italic), font name, and bounding boxes
- Maintains page number information for each text element

### 2. Heading Detection Algorithm
The system uses a scoring-based approach that considers multiple factors:

**Font Analysis:**
- Relative font size compared to document average
- Bold formatting detection via font flags
- Font size thresholds for different heading levels

**Content Analysis:**
- Keyword matching for common heading terms
- Numbered section detection (1., 2.1, etc.)
- Text length analysis (headings are typically shorter)
- Title case pattern recognition

**Structural Analysis:**
- Position within document (titles typically on first pages)
- Bounding box analysis for layout understanding

### 3. Title Extraction
- Focuses on first 1-2 pages of document
- Identifies largest font sizes
- Filters out numeric-only content
- Applies title-specific pattern matching

### 4. Heading Classification
Uses dynamic thresholds based on document characteristics:
- **H1**: Large font size, high relative size ratio (≥1.3x average)
- **H2**: Medium-large font size, moderate relative size (≥1.2x average)  
- **H3**: Medium font size, slight size increase (≥1.1x average)

## Libraries Used

- **PyMuPDF (fitz)**: Primary PDF processing library
  - Lightweight and fast
  - Excellent font and formatting extraction
  - No ML model dependencies
  - Size: ~15MB

## Key Features

- **Robust Detection**: Doesn't rely solely on font sizes
- **Multilingual Support**: Works with Unicode text (including Japanese, Arabic, etc.)
- **Performance Optimized**: Processes 50-page PDFs in under 5 seconds
- **Offline Operation**: No network dependencies
- **Memory Efficient**: Processes documents page by page

## Architecture

```
PDFStructureExtractor
├── extract_text_with_formatting()  # Extract text with font info
├── is_likely_heading()             # Multi-factor heading detection
├── classify_heading_level()        # Determine H1/H2/H3 levels
├── extract_title()                 # Title extraction logic
└── extract_headings()              # Main heading extraction
```

## Building and Running

### Build the Docker Image
```bash
docker build --platform linux/amd64 -t pdf-extractor:latest .
```

### Run the Solution
```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-extractor:latest
```

### Expected File Structure
```
input/
├── document1.pdf
├── document2.pdf
└── sample.pdf

output/
├── document1.json
├── document2.json
└── sample.json
```

### Example Output Format
```json
{
  "title": "Understanding Artificial Intelligence",
  "outline": [
    {
      "level": "H1",
      "text": "Introduction to AI",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "Machine Learning Fundamentals",
      "page": 3
    },
    {
      "level": "H3",
      "text": "Supervised Learning",
      "page": 5
    }
  ]
}
```

## Performance Characteristics

- **Speed**: ~0.1-0.2 seconds per page
- **Memory**: Low memory footprint with page-by-page processing
- **Accuracy**: High precision through multi-factor analysis
- **Compatibility**: Works with various PDF formats and languages

## Error Handling

- Graceful handling of corrupted PDFs
- Fallback mechanisms for difficult documents
- Comprehensive logging for debugging
- Empty document handling

## Testing Recommendations

Test with various document types:
- Academic papers with numbered sections
- Technical manuals with nested headings
- Multilingual documents
- Documents with irregular formatting
- Scanned PDFs (with embedded text)

## Limitations

- Requires text-based PDFs (not pure image PDFs without OCR)
- Performance depends on document complexity
- May need fine-tuning for specific document formats

## Future Enhancements

- OCR integration for scanned documents
- Table of contents extraction
- Document metadata extraction
- Support for additional heading levels (H4, H5, H6)
