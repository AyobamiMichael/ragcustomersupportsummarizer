# scripts/download_models.py
"""
Download and cache all required ML models for RAG Summarizer
Run this from the project root: python scripts/download_models.py
"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("RAG SUMMARIZER - MODEL DOWNLOAD SCRIPT")
print("=" * 70)

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Change to backend directory for model cache
os.chdir(backend_path)
print(f"\nWorking directory: {os.getcwd()}")

# Create models directory
models_dir = Path("./models")
models_dir.mkdir(exist_ok=True)
print(f"✅ Models directory: {models_dir.absolute()}")


def download_sentence_transformer():
    """Download sentence transformer model"""
    print("\n" + "=" * 70)
    print("1. DOWNLOADING SENTENCE TRANSFORMER MODEL")
    print("=" * 70)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model_name = "all-MiniLM-L6-v2"
        print(f"\nModel: {model_name}")
        print(f"Size: ~90 MB")
        print(f"Downloading...")
        
        model = SentenceTransformer(
            model_name,
            cache_folder=str(models_dir)
        )
        
        print(f"✅ Downloaded successfully to {models_dir.absolute()}")
        
        # Test the model
        print(f"\nTesting model...")
        test_sentences = ["This is a test.", "This is another test."]
        embeddings = model.encode(test_sentences)
        print(f"✅ Model working! Embedding shape: {embeddings.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading sentence transformer: {e}")
        return False


def download_nltk_data():
    """Download NLTK data"""
    print("\n" + "=" * 70)
    print("2. DOWNLOADING NLTK DATA")
    print("=" * 70)
    
    try:
        import nltk
        
        datasets = ['punkt', 'stopwords']
        
        for dataset in datasets:
            print(f"\nDownloading {dataset}...")
            nltk.download(dataset, quiet=False)
            print(f"✅ {dataset} downloaded")
        
        # Test NLTK
        print(f"\nTesting NLTK...")
        from nltk.tokenize import sent_tokenize
        test_text = "This is sentence one. This is sentence two."
        sentences = sent_tokenize(test_text)
        print(f"✅ NLTK working! Tokenized {len(sentences)} sentences")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading NLTK data: {e}")
        return False


def download_spacy_model():
    """Download spaCy model"""
    print("\n" + "=" * 70)
    print("3. DOWNLOADING SPACY MODEL")
    print("=" * 70)
    
    try:
        import spacy
        
        model_name = "en_core_web_sm"
        print(f"\nModel: {model_name}")
        print(f"Size: ~15 MB")
        
        # Check if already installed
        try:
            nlp = spacy.load(model_name)
            print(f"✅ {model_name} already installed")
        except OSError:
            print(f"Downloading {model_name}...")
            os.system(f'python -m spacy download {model_name}')
            print(f"✅ {model_name} downloaded")
        
        # Test spaCy
        print(f"\nTesting spaCy...")
        nlp = spacy.load(model_name)
        doc = nlp("This is a test sentence.")
        print(f"✅ spaCy working! Processed {len(doc)} tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading spaCy model: {e}")
        return False


def verify_all_models():
    """Verify all models are working"""
    print("\n" + "=" * 70)
    print("4. VERIFYING ALL MODELS")
    print("=" * 70)
    
    all_ok = True
    
    # Check sentence transformer
    print("\n📦 Sentence Transformer:")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=str(models_dir))
        print("   ✅ Loaded and ready")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_ok = False
    
    # Check NLTK
    print("\n📦 NLTK:")
    try:
        from nltk.tokenize import sent_tokenize
        from nltk.corpus import stopwords
        sent_tokenize("Test.")
        stopwords.words('english')
        print("   ✅ Loaded and ready")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_ok = False
    
    # Check spaCy
    print("\n📦 spaCy:")
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("   ✅ Loaded and ready")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_ok = False
    
    return all_ok


def main():
    """Main download function"""
    results = {
        'sentence_transformer': False,
        'nltk': False,
        'spacy': False
    }
    
    # Download all models
    results['sentence_transformer'] = download_sentence_transformer()
    results['nltk'] = download_nltk_data()
    results['spacy'] = download_spacy_model()
    
    # Verify everything
    all_verified = verify_all_models()
    
    # Print summary
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    
    for model, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{model:30} {status}")
    
    if all(results.values()) and all_verified:
        print("\n🎉 ALL MODELS DOWNLOADED AND VERIFIED!")
        print("\nYou can now run the server:")
        print("  cd backend")
        print("  uvicorn src.main:app --reload")
    else:
        print("\n⚠️  Some models failed to download")
        print("Try installing manually:")
        print("  pip install sentence-transformers nltk spacy")
        print("  python -m spacy download en_core_web_sm")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
