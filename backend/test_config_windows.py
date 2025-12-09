"""
Enhanced debug script for Windows
Run this: python test_config_windows.py
"""

import os
from pathlib import Path
import sys

print("=" * 70)
print("WINDOWS CONFIGURATION DEBUG SCRIPT")
print("=" * 70)

# Check Python version
print(f"\n1. Python Version: {sys.version}")
print(f"   Platform: {sys.platform}")

# Check current directory
current_dir = Path.cwd()
print(f"\n2. Current Directory: {current_dir}")

# Check for .env file
env_locations = [
    Path(".env"),
    Path("../.env"),
    Path("../../.env"),
    current_dir / ".env",
    current_dir.parent / ".env",
]

print(f"\n3. Searching for .env file:")
env_found = None
for env_path in env_locations:
    abs_path = env_path.resolve()
    exists = abs_path.exists()
    print(f"   {'✅' if exists else '❌'} {abs_path}")
    if exists and not env_found:
        env_found = abs_path

if not env_found:
    print(f"\n❌ ERROR: .env file not found in any location!")
    print(f"\nCreate .env file at: {current_dir.parent / '.env'}")
    sys.exit(1)

print(f"\n✅ Using .env file: {env_found}")

# Read .env file content
print(f"\n4. Checking .env file content:")
try:
    with open(env_found, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print(f"   Total lines: {len(lines)}")
    
    # Check for GROQ_API_KEY
    groq_lines = [line.strip() for line in lines if "GROQ_API_KEY" in line and not line.strip().startswith("#")]
    
    if groq_lines:
        print(f"   ✅ Found GROQ_API_KEY in .env:")
        for line in groq_lines:
            if "=" in line:
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                if value and value not in ["your_key_here", "gsk_your_key_here"]:
                    print(f"      {key}={value[:15]}...{value[-8:] if len(value) > 23 else ''}")
                else:
                    print(f"      ⚠️  {key}={value} (PLACEHOLDER - Replace with actual key!)")
    else:
        print(f"   ❌ GROQ_API_KEY not found in .env file!")
        print(f"   First 10 lines of .env:")
        for i, line in enumerate(lines[:10], 1):
            print(f"      {i}: {line.rstrip()}")
        
except Exception as e:
    print(f"   ❌ Error reading .env: {e}")

# Try loading with python-dotenv
print(f"\n5. Loading with python-dotenv:")
try:
    from dotenv import load_dotenv
    
    # Clear any existing GROQ_API_KEY
    if "GROQ_API_KEY" in os.environ:
        print(f"   ℹ️  Clearing existing GROQ_API_KEY from environment")
        del os.environ["GROQ_API_KEY"]
    
    # Load .env file
    loaded = load_dotenv(env_found, override=True)
    print(f"   load_dotenv(): {'✅ Success' if loaded else '❌ Failed'}")
    
    # Check if loaded
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"   ✅ GROQ_API_KEY loaded: {groq_key[:15]}...{groq_key[-8:]}")
    else:
        print(f"   ❌ GROQ_API_KEY still not in environment after load_dotenv()")
        print(f"   All environment variables with 'GROQ':")
        for key, value in os.environ.items():
            if "GROQ" in key.upper():
                print(f"      {key}={value[:20]}...")
        
except ImportError:
    print("   ❌ python-dotenv not installed!")
    print("   Install it: pip install python-dotenv")
    sys.exit(1)

# Try loading Settings with Pydantic
print(f"\n6. Loading with Pydantic Settings:")
try:
    # Add parent directory to path
    sys.path.insert(0, str(current_dir))
    
    from src.config import get_settings
    
    settings = get_settings()
    print(f"   ✅ Settings loaded successfully")
    
    if settings.GROQ_API_KEY:
        print(f"   ✅ GROQ_API_KEY: {settings.GROQ_API_KEY[:15]}...{settings.GROQ_API_KEY[-8:]}")
    else:
        print(f"   ❌ GROQ_API_KEY: None (not loaded)")
        
    print(f"   LLM_MODEL: {settings.LLM_MODEL}")
    print(f"   API_PORT: {settings.API_PORT}")
    
except Exception as e:
    print(f"   ❌ Error loading settings: {e}")
    import traceback
    traceback.print_exc()

# Final check
print(f"\n7. Final Verification:")
if os.getenv("GROQ_API_KEY"):
    print(f"   ✅ GROQ_API_KEY is available in environment")
else:
    print(f"   ❌ GROQ_API_KEY is NOT available in environment")
    print(f"\n   SOLUTION:")
    print(f"   1. Make sure .env has: GROQ_API_KEY=gsk_your_actual_key")
    print(f"   2. No spaces around =")
    print(f"   3. No quotes needed")
    print(f"   4. Restart your terminal/IDE")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)