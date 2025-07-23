import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
from collections import Counter
from typing import Dict, List, Optional
import hashlib
import spacy

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ContentProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        # Try to load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """Extract important keywords from text"""
        cleaned_text = self.clean_text(text.lower())
        
        # Tokenize
        words = word_tokenize(cleaned_text)
        
        # Remove stopwords and short words
        filtered_words = [
            self.stemmer.stem(word) for word in words 
            if word not in self.stop_words and len(word) > 2 and word.isalpha()
        ]
        
        # Get most common words
        word_freq = Counter(filtered_words)
        return [word for word, freq in word_freq.most_common(num_keywords)]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text using spaCy"""
        if not self.nlp:
            return {"persons": [], "organizations": [], "locations": [], "misc": []}
        
        doc = self.nlp(text)
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "misc": []
        }
        
        for ent in doc.ents:
            if ent.label_ in ["PERSON"]:
                entities["persons"].append(ent.text)
            elif ent.label_ in ["ORG"]:
                entities["organizations"].append(ent.text)
            elif ent.label_ in ["GPE", "LOC"]:
                entities["locations"].append(ent.text)
            else:
                entities["misc"].append(ent.text)
        
        return entities
    
    def calculate_readability_score(self, text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        if len(sentences) == 0 or len(words) == 0:
            return 0.0
        
        # Count syllables (simple approximation)
        syllables = sum([self.count_syllables(word) for word in words])
        
        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * (len(words) / len(sentences))) - (84.6 * (syllables / len(words)))
        return max(0, min(100, score))
    
    def count_syllables(self, word: str) -> int:
        """Simple syllable counting"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def generate_summary(self, text: str, num_sentences: int = 3) -> str:
        """Generate a simple extractive summary"""
        sentences = sent_tokenize(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # Score sentences based on word frequency
        word_freq = Counter(word_tokenize(text.lower()))
        
        sentence_scores = {}
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            score = sum([word_freq[word] for word in words if word not in self.stop_words])
            sentence_scores[sentence] = score
        
        # Get top sentences
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
        
        # Maintain original order
        summary_sentences = []
        for sentence in sentences:
            if any(sentence == sent[0] for sent in top_sentences):
                summary_sentences.append(sentence)
                if len(summary_sentences) == num_sentences:
                    break
        
        return ' '.join(summary_sentences)
    
    def detect_language(self, text: str) -> str:
        """Simple language detection (basic implementation)"""
        # This is a very basic implementation
        # For production, use langdetect library
        english_words = set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        words = set(word_tokenize(text.lower()))
        
        english_score = len(words.intersection(english_words)) / len(words) if words else 0
        
        return 'en' if english_score > 0.1 else 'unknown'
    
    def calculate_content_hash(self, text: str) -> str:
        """Generate hash for duplicate detection"""
        cleaned_text = self.clean_text(text.lower())
        return hashlib.md5(cleaned_text.encode()).hexdigest()
    
    def is_spam_content(self, text: str) -> bool:
        """Basic spam detection"""
        spam_indicators = [
            'click here', 'buy now', 'limited time', 'act now',
            'free money', 'guaranteed', 'no risk', 'call now',
            'urgent', 'exclusive', 'special offer'
        ]
        
        text_lower = text.lower()
        spam_count = sum(1 for indicator in spam_indicators if indicator in text_lower)
        
        # Also check for excessive capitalization
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        
        return spam_count >= 3 or caps_ratio > 0.5
