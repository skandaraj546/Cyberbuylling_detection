"""
Quick patch to enable CLIP image detection
Run this ONCE, then restart your app
"""

import fileinput
import sys

print("="*60)
print("ENABLING CLIP IMAGE DETECTION")
print("="*60)

# Read the app.py file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the location to insert CLIP code
search_text = "        # Method 2: OCR text extraction and analysis"

if search_text in content:
    # Insert CLIP code before OCR
    clip_code = """        # Method 2: Local AI Image Analysis (CLIP model - FREE, no API)
        try:
            from local_image_analyzer import get_local_analyzer
            print("[LOCAL AI] Loading CLIP model for image analysis...")
            local_analyzer = get_local_analyzer()
            if local_analyzer.is_available():
                ai_toxic, ai_labels, ai_scores = local_analyzer.analyze_image(image_path)
                if ai_toxic:
                    is_toxic = True
                    all_labels.extend(ai_labels)
                    all_scores.update(ai_scores)
                    print(f"[LOCAL AI] ✗ TOXIC image detected: {ai_labels}")
                else:
                    print("[LOCAL AI] ✓ Image appears safe")
            else:
                print("[LOCAL AI] ⚠️  CLIP model not available")
        except Exception as e:
            print(f"[LOCAL AI] ⚠️  Error: {e}")
        
        # Method 3: OCR text extraction and analysis"""
    
    # Replace
    new_content = content.replace(search_text, clip_code)
    
    # Write back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ CLIP detection enabled!")
    print("\nNow restart your app:")
    print("   python app.py")
    print("\nThe CLIP model will:")
    print("   1. Download automatically on first run (~500MB)")
    print("   2. Detect cyberbullying themes in images")
    print("   3. Work without Tesseract OCR")
    print("="*60)
else:
    print("❌ Could not find insertion point in app.py")
    print("The file may have been modified already")
    print("="*60)
