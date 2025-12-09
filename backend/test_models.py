"""
Test if all models are loaded correctly
Run from backend folder: python test_models.py
"""

import sys
from pathlib import Path

print("=" * 70)
print("MODEL VERIFICATION TEST")
print("=" * 70)

# Test 1: Sentence Transformer
print("\n1. Testing Sentence Transformer...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models')
    
    # Test encoding
    sentences = ["Hello world", "How are you?"]
    embeddings = model.encode(sentences)
    
    print(f"   ✅ Model loaded")
    print(f"   ✅ Embedding shape: {embeddings.shape}")
    print(f"   ✅ Model type: {type(model)}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: NLTK
print("\n2. Testing NLTK...")
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.corpus import stopwords
    
    # Test tokenization
    text = "This is sentence one. This is sentence two."
    sentences = sent_tokenize(text)
    stops = stopwords.words('english')
    
    print(f"   ✅ NLTK loaded")
    print(f"   ✅ Tokenized {len(sentences)} sentences")
    print(f"   ✅ Loaded {len(stops)} stopwords")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 3: spaCy
print("\n3. Testing spaCy...")
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    
    # Test processing
    doc = nlp("This is a test sentence with some words.")
    
    print(f"   ✅ spaCy loaded")
    print(f"   ✅ Processed {len(doc)} tokens")
    print(f"   ✅ Model: en_core_web_sm")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 4: Full Integration
print("\n4. Testing Full Integration...")
try:
    from src.services.embedding_service import EmbeddingService
    from src.services.preprocessor import PreprocessorService
    from src.services.textrank_service import TextRankService
    
    # Initialize services
    embeddings = EmbeddingService()
    preprocessor = PreprocessorService()
    textrank = TextRankService()
    
    print(f"   ✅ All services initialized")
    
    # Test embedding service
    test_sentences = ["This is a test.", "Another test sentence."]
    embeddings._load_model()  # Force load
    result = embeddings.encode_sentences(test_sentences)
    
    print(f"   ✅ Embedding service working")
    print(f"   ✅ Model loaded: {embeddings.model is not None}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("🎉 ALL MODELS VERIFIED AND WORKING!")
print("=" * 70)
print("\nYour application is ready to use:")
print("  uvicorn src.main:app --reload")
print("\n")