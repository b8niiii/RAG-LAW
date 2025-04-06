# article_splitter.py
import re

class ArticleSplitter:
    """
    A class responsible for parsing a legal code PDF and splitting it into articles.
    Each article is returned as a dictionary with 'article_number' and 'text' keys.
    """

    def __init__(self, skip_patterns=None):
        """
        Initialize the ArticleSplitter with optional skip patterns.

        Args:
            skip_patterns (list): A list of regex patterns. Lines matching any of these
                                  will be ignored (e.g., headers, footers).
        """
        # Default skip patterns include:
        # - Empty lines
        # - Repeated header/footer text (e.g., publisher info)
        # - Page numbers
        # - The six "Libro ..." headers from the codice civile
        self.skip_patterns = skip_patterns or [
            r"^\s*$",  # Empty or whitespace-only lines
            r"^Altalex eBook",  
            r"^Collana Codici Altalex",  
            r"^CODICE CIVILE",  
            r"^\d+$",  # Lines with only digits (often page numbers)
            r"^Libro I\s*-\s*Delle persone e della famiglia",
            r"^Libro II\s*-\s*Delle successioni",
            r"^Libro III\s*-\s*Della proprietà",
            r"^Libro IV\s*-\s*Delle obbligazioni",
            r"^Libro V\s*-\s*Del lavoro",
            r"^Libro VI\s*[–-]\s*Della tutela dei diritti",  # Handles both en-dash and hyphen
            r"(?i)^\s*capo\s+(\d+|[IVXLC]+)\b.*",   # Skip lines starting with "capo" followed by a number or Roman numeral
            r"(?i)^\s*titolo\s+(\d+|[IVXLC]+)\b.*",  # Skip lines starting with "titolo" followed by a number or Roman numeral
         ]

        # Regex to match article headings.
        # This pattern handles variations like "Art. 7", "Art 7.", or uppercase "ART. 7."
        self.article_pattern = re.compile(r"^\s*Art\.?\s*(\d+)\s*\.?")
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from the provided PDF file using pdfplumber.
        
        Args:
            pdf_path (str): Path to the PDF file.
            
        Returns:
            str: The extracted text from the PDF.
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    
    
    def skip_line(self, line: str) -> bool:
        """
        Check if a line should be skipped based on any of the skip patterns.

        Args:
            line (str): The line to check.

        Returns:
            bool: True if the line should be skipped, False otherwise.
        """
        for pattern in self.skip_patterns:
            if re.match(pattern, line.strip()):
                return True
        return False

    def split_articles(self, text: str):
        """
        Split the raw text into a list of article dictionaries.
        
        Args:
            text (str): The entire PDF text extracted as a single string.
        
        Returns:
            list: A list of dictionaries, each with "article_number" and "text".
        """
        articles = []  # List to store all parsed articles
        current_article_number = None  # Variable to keep track of the current article number
        current_text_lines = []  # List to accumulate text lines for the current article

        # Iterate over each line from the extracted text
        for line in text.splitlines():
            # Remove any leading or trailing whitespace from the line
            line = line.strip()

            # Skip lines that match unwanted patterns (headers, footers, page numbers, "Libro" headers, etc.)
            if self.skip_line(line):
                continue

            # Check if the current line matches the article heading pattern (e.g., "Art. 7")
            match = self.article_pattern.match(line)
            if match:
                # If we have been collecting an article, save it before starting a new one
                if current_article_number is not None:
                    articles.append({
                        "article_number": current_article_number,
                        "text": " ".join(current_text_lines).strip()  # Join all lines into one text block
                    })
                    current_text_lines = []  # Reset the accumulator for the next article

                # Update the current article number using the captured group from the regex match
                current_article_number = match.group(1)

                # Remove the matched article header from the line
                # If there's remaining text on the same line, add it to the current article's text
                remaining_text = line[match.end():].strip()
                if remaining_text:
                    current_text_lines.append(remaining_text)
            else:
                # If the line does not start a new article heading, and we are in the middle of an article,
                # accumulate the line into the current article's text.
                if current_article_number is not None:
                    current_text_lines.append(line)
                # Optionally, if no article has started yet, you could handle preamble text here.

        # After processing all lines, if an article was being built, add it to the articles list
        if current_article_number is not None:
            articles.append({
                "article_number": current_article_number,
                "text": " ".join(current_text_lines).strip()
            })

        # Return the list of article dictionaries
        return articles

