"""
Test CLIP model directly on the toxic image
"""
import sys
import os

print("="*60)
print("TESTING CLIP MODEL DIRECTLY")
print("="*60)

# Test if local_image_analyzer works
try:
    from local_image_analyzer import get_local_analyzer
    print("\n✅ local_image_analyzer imported successfully")
    
    # Get analyzer
    analyzer = get_local_analyzer()
    
    if analyzer.is_available():
        print("✅ CLIP model is available")
        
        # Test on the toxic image
        test_image = "test_cyberbullying_scene.png"
        if os.path.exists(test_image):
            print(f"\n🔍 Testing on: {test_image}")
            print("-"*60)
            
            is_toxic, labels, scores = analyzer.analyze_image(test_image)
            
            print("-"*60)
            print(f"\n📊 RESULTS:")
            print(f"   Is Toxic: {is_toxic}")
            print(f"   Labels: {labels}")
            print(f"   Scores: {scores}")
            
            if is_toxic:
                print("\n✅ SUCCESS! Image detected as TOXIC")
            else:
                print("\n❌ FAILED! Image NOT detected as toxic")
                print("   This means the threshold is too high")
                print("   Or the CLIP model needs better prompts")
        else:
            print(f"\n❌ Test image not found: {test_image}")
            print("   Run: python generate_test_images.py first")
    else:
        print("❌ CLIP model NOT available")
        print("   Check if transformers and torch are installed")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
