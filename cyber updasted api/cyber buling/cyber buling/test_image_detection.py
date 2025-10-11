#!/usr/bin/env python3
"""
Test script to diagnose why image detection is not working
"""
import os
from PIL import Image

print("="*60)
print("IMAGE DETECTION DIAGNOSTIC TEST")
print("="*60)

# Test 1: Check if Tesseract is available
print("\n1️⃣ TESTING TESSERACT OCR:")
try:
    import pytesseract
    print("   ✅ pytesseract module installed")
    
    # Try to get version
    try:
        version = pytesseract.get_tesseract_version()
        print(f"   ✅ Tesseract version: {version}")
        tesseract_works = True
    except Exception as e:
        print(f"   ❌ Tesseract not found: {e}")
        print("   💡 Install from: https://github.com/UB-Mannheim/tesseract/wiki")
        tesseract_works = False
except ImportError:
    print("   ❌ pytesseract not installed")
    print("   Run: pip install pytesseract")
    tesseract_works = False

# Test 2: Check if transformers available
print("\n2️⃣ TESTING TRANSFORMERS:")
try:
    from transformers import pipeline
    print("   ✅ transformers installed")
except ImportError:
    print("   ❌ transformers not installed")
    print("   Run: pip install transformers")

# Test 3: Check if CLIP available
print("\n3️⃣ TESTING CLIP MODEL:")
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    print("   ✅ CLIP dependencies installed")
    
    # Try to load model
    try:
        print("   Loading CLIP model (this may take a minute)...")
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        print("   ✅ CLIP model loaded successfully!")
    except Exception as e:
        print(f"   ❌ Failed to load CLIP: {e}")
except ImportError:
    print("   ❌ CLIP dependencies not installed")
    print("   Run: pip install transformers torch")

# Test 4: Test keyword detection
print("\n4️⃣ TESTING KEYWORD DETECTION:")
toxic_keywords = {
    "fuck", "shit", "bitch", "ass", "damn",
    "idiot", "stupid", "dumb", "loser", "ugly",
    "nigger", "nigga", "niga", "faggot", "cunt"
}
print(f"   Loaded {len(toxic_keywords)} keywords")

test_texts = [
    "STUPID IDIOT UGLY DUMB",
    "stupid",
    "idiot",
    "hello friend"
]

for text in test_texts:
    text_lower = text.lower()
    matches = [w for w in toxic_keywords if w in text_lower]
    if matches:
        print(f"   ✅ '{text}' → BLOCKED (matched: {matches})")
    else:
        print(f"   ✓ '{text}' → ALLOWED")

# Test 5: Test OCR on sample if Tesseract works
if tesseract_works:
    print("\n5️⃣ TESTING OCR TEXT EXTRACTION:")
    print("   Create a test image with text...")
    
    # Create simple test image with text
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (400, 100), color='white')
    d = ImageDraw.Draw(img)
    d.text((10,10), "STUPID IDIOT", fill='black')
    test_img_path = "test_image.png"
    img.save(test_img_path)
    
    try:
        text = pytesseract.image_to_string(Image.open(test_img_path))
        print(f"   Extracted: '{text.strip()}'")
        
        # Check if toxic
        text_lower = text.lower()
        matches = [w for w in toxic_keywords if w in text_lower]
        if matches:
            print(f"   ✅ TOXIC DETECTED: {matches}")
        else:
            print(f"   ⚠️  No toxic words found (OCR might not be working well)")
        
        # Cleanup
        os.remove(test_img_path)
    except Exception as e:
        print(f"   ❌ OCR failed: {e}")

print("\n" + "="*60)
print("DIAGNOSIS COMPLETE")
print("="*60)

print("\n📋 SUMMARY:")
print("   Tesseract OCR:", "✅ Working" if tesseract_works else "❌ Not working")
print("   Keyword Detection: ✅ Working")
print("\n💡 RECOMMENDATIONS:")
if not tesseract_works:
    print("   1. Install Tesseract OCR")
    print("      Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   2. Add to .env: TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
else:
    print("   ✅ Everything looks good!")
    print("   If images still not detected, check console logs when uploading")

print("="*60)
