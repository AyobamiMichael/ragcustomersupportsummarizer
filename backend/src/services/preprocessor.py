"""
Text preprocessing service with rule-based extraction
"""

import re
from typing import Dict, List, Tuple
import nltk
from nltk.tokenize import sent_tokenize
from bs4 import BeautifulSoup


from ..config import get_settings, REGEX_PATTERNS, PRIORITY_KEYWORDS, KNOWN_SECTIONS
from ..models.schemas import PreprocessingResult


class PreprocessorService:
    """Service for text preprocessing and structural extraction"""
    
    def __init__(self):
        self.settings = get_settings()
        self._ensure_nltk_data()
    

    def _ensure_nltk_data(self):
        """Download required NLTK data if not present"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
    
    def _ensure_nltk_data(self):
        """Download required NLTK data if not present"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
    
    def preprocess(self, text: str) -> PreprocessingResult:
        """
        Main preprocessing pipeline
        
        Args:
            text: Raw input text
            
        Returns:
            PreprocessingResult with cleaned text and extracted sections
        """
        # Step 1: Basic cleaning
        cleaned = self._clean_text(text)
        
        # Step 2: Extract structural sections
        sections = self._extract_sections(cleaned)
        
        # Step 3: Additional metadata
        metadata = self._extract_metadata(cleaned)
        
        return PreprocessingResult(
            cleaned_text=cleaned,
            sections=sections,
            metadata=metadata
        )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize input text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove HTML tags
        text = BeautifulSoup(text, 'lxml').get_text()
        
        # Remove extra whitespace
        text = REGEX_PATTERNS['whitespace'].sub(' ', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract structural sections from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Dictionary mapping section names to content
        """
        sections = {}
        lines = text.split('\n')
        
        current_section = 'body'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            if self._is_section_header(line):
                # Save previous section
                if current_content:
                    sections[current_section] = ' '.join(current_content)
                
                # Start new section
                current_section = line.rstrip(':').lower().strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = ' '.join(current_content)
        
        # If no sections found, treat entire text as body
        if not sections or (len(sections) == 1 and 'body' in sections):
            sections['body'] = text
        
        return sections
    

    def _is_section_header(self, line: str) -> bool:
        """
        Check if a line is a section header
        
        Args:
            line: Text line
            
        Returns:
            True if line is a section header
        """
        # Pattern: "Section Name:" at start of line
        if REGEX_PATTERNS['section_header'].match(line):
            section_name = line.rstrip(':').lower().strip()
            return any(known in section_name for known in KNOWN_SECTIONS)
        return False
    
    
    def _extract_metadata(self, text: str) -> Dict[str, any]:
        """
        Extract metadata from text
        
        Args:
            text: Cleaned text
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Extract ticket IDs
        ticket_ids = REGEX_PATTERNS['ticket_id'].findall(text)
        if ticket_ids:
            metadata['ticket_ids'] = ticket_ids
        
        # Extract emails
        emails = REGEX_PATTERNS['email'].findall(text)
        if emails:
            metadata['emails'] = emails[:3]  # Limit for privacy
        
        # Extract URLs
        urls = REGEX_PATTERNS['url'].findall(text)
        if urls:
            metadata['urls'] = urls[:5]
        
        # Calculate text statistics
        sentences = sent_tokenize(text)
        words = text.split()
        
        metadata['stats'] = {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0
        }
        
        return metadata
    

    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        sentences = sent_tokenize(text)
        
        # Filter sentences by length
        filtered = []
        for sent in sentences:
            word_count = len(sent.split())
            if (self.settings.MIN_SENTENCE_LENGTH <= word_count <= 
                self.settings.MAX_SENTENCE_LENGTH):
                filtered.append(sent.strip())
        
        return filtered
    
    def score_sentence_heuristic(self, sentence: str, position: int, 
                                 total: int) -> float:
        """
        Apply heuristic scoring to a sentence
        
        Args:
            sentence: The sentence to score
            position: Position in document (0-indexed)
            total: Total number of sentences
            
        Returns:
            Heuristic score
        """
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Keyword matching
        for keyword, weight in PRIORITY_KEYWORDS.items():
            if keyword in sentence_lower:
                score += weight
        
        # Position bonus (first and last sentences often important)
        if position == 0:
            score += 1.0
        elif position == total - 1:
            score += 0.8
        elif position < 3:
            score += 0.5
        
        # Length bonus (prefer medium-length sentences)
        word_count = len(sentence.split())
        if 10 <= word_count <= 30:
            score += 1.0
        elif 8 <= word_count < 10 or 30 < word_count <= 40:
            score += 0.5
        
        # Question bonus (questions often indicate issues)
        if '?' in sentence:
            score += 0.5
        
        return score
    

    def remove_boilerplate(self, text: str) -> str:
        """
        Remove common boilerplate text
        
        Args:
            text: Input text
            
        Returns:
            Text with boilerplate removed
        """
        boilerplate_patterns = [
            r'This email is confidential.*',
            r'Please do not reply to this email.*',
            r'Sent from my .*',
            r'Get Outlook for .*',
            r'\[cid:.*?\]',
            r'Original Message.*?From:.*?To:.*?Subject:',
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()