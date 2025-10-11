"""
Generate test images for testing detection
"""
from PIL import Image, ImageDraw, ImageFont

print("="*60)
print("GENERATING TEST IMAGES")
print("="*60)

# Test Image 1: Toxic text
print("\n1. Creating toxic_image.png...")
img1 = Image.new('RGB', (600, 400), color='black')
d1 = ImageDraw.Draw(img1)
try:
    font = ImageFont.truetype("arial.ttf", 40)
except:
    font = ImageFont.load_default()

d1.text((50, 50), "STUPID", fill='red', font=font)
d1.text((50, 120), "IDIOT", fill='red', font=font)
d1.text((50, 190), "UGLY", fill='red', font=font)
d1.text((50, 260), "DUMB", fill='red', font=font)
img1.save('test_toxic_image.png')
print("   ✅ Created: test_toxic_image.png")
print("   Expected: Should be BLOCKED")

# Test Image 2: Clean image
print("\n2. Creating clean_image.png...")
img2 = Image.new('RGB', (600, 400), color='lightblue')
d2 = ImageDraw.Draw(img2)
d2.text((50, 150), "Hello Friend!", fill='white', font=font)
d2.text((50, 220), "Have a nice day!", fill='white', font=font)
img2.save('test_clean_image.png')
print("   ✅ Created: test_clean_image.png")
print("   Expected: Should be ALLOWED")

# Test Image 3: Cyberbullying scene (simulated)
print("\n3. Creating cyberbullying_scene.png...")
img3 = Image.new('RGB', (600, 400), color='darkred')
d3 = ImageDraw.Draw(img3)
# Draw a sad face
d3.ellipse([250, 100, 350, 200], fill='white')
d3.ellipse([270, 130, 290, 150], fill='black')  # Left eye
d3.ellipse([310, 130, 330, 150], fill='black')  # Right eye
d3.arc([270, 160, 330, 180], 0, 180, fill='black', width=3)  # Sad mouth
# Add toxic words around
d3.text((50, 50), "LOSER", fill='orange', font=font)
d3.text((400, 50), "HATE", fill='orange', font=font)
d3.text((50, 320), "WORTHLESS", fill='orange', font=font)
img3.save('test_cyberbullying_scene.png')
print("   ✅ Created: test_cyberbullying_scene.png")
print("   Expected: Should be BLOCKED")

print("\n" + "="*60)
print("TEST IMAGES GENERATED")
print("="*60)
print("\nYou can now upload these images to test:")
print("   1. test_toxic_image.png → Should be BLOCKED")
print("   2. test_clean_image.png → Should be ALLOWED")
print("   3. test_cyberbullying_scene.png → Should be BLOCKED")
print("="*60)
