"""
Local Image Analyzer using FREE Hugging Face models
NO API CALLS - Everything runs on your machine
"""
import os
from typing import Tuple, List, Dict
from PIL import Image

# Try to import CLIP model for image understanding
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False

# Try to import image classification model
try:
    from transformers import pipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False


class LocalImageAnalyzer:
    """
    Analyzes images using FREE local models from Hugging Face
    - CLIP: Understands image content
    - Image Classification: Detects NSFW/inappropriate content
    - Zero-shot classification: Detects cyberbullying themes
    """
    
    def __init__(self):
        self.clip_model = None
        self.clip_processor = None
        self.nsfw_classifier = None
        self.zero_shot_classifier = None
        
        print("\n[LOCAL IMAGE ANALYZER] Initializing...")
        
        # Initialize CLIP model (understands images + text)
        if CLIP_AVAILABLE:
            try:
                print("[CLIP] Loading openai/clip-vit-base-patch32...")
                self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                print("[CLIP] ✅ Model loaded successfully")
            except Exception as e:
                print(f"[CLIP] ❌ Failed to load: {e}")
        else:
            print("[CLIP] ❌ Not available - install transformers and torch")
        
        # Initialize zero-shot classifier (detects any concept)
        if PIPELINE_AVAILABLE:
            try:
                print("[ZERO-SHOT] Loading facebook/bart-large-mnli...")
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
                print("[ZERO-SHOT] ✅ Model loaded successfully")
            except Exception as e:
                print(f"[ZERO-SHOT] ❌ Failed to load: {e}")
        
        print("[LOCAL IMAGE ANALYZER] ✅ Initialization complete\n")
    
    def analyze_with_clip(self, image_path: str) -> Tuple[bool, List[str], Dict[str, float]]:
        """
        Use CLIP to understand if image contains toxic/bullying content
        """
        if not self.clip_model or not self.clip_processor:
            return False, [], {}
        
        try:
            print(f"[CLIP] Analyzing image: {os.path.basename(image_path)}")
            
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Define toxic/bullying concepts to check (more specific for text in images)
            toxic_concepts = [
                "text saying stupid",
                "text saying idiot", 
                "text saying ugly",
                "text saying dumb",
                "insulting words",
                "mean text messages",
                "cyberbullying text",
                "harassment messages",
                "hate speech text",
                "offensive words",
                "bullying messages",
                "threatening text",
                "person being bullied",
                "sad person with mean words"
            ]
            
            safe_concepts = [
                "landscape",
                "nature",
                "food",
                "animals",
                "people smiling",
                "normal photo"
            ]
            
            # Process image and text
            inputs = self.clip_processor(
                text=toxic_concepts + safe_concepts,
                images=image,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77
            )
            
            # Get predictions
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)[0]
            
            # Get scores for toxic concepts
            toxic_scores = {}
            max_toxic_score = 0.0
            detected_labels = []
            
            for i, concept in enumerate(toxic_concepts):
                score = float(probs[i])
                toxic_scores[concept] = score
                if score > 0.15:  # Even lower threshold for better detection
                    detected_labels.append(concept)
                    max_toxic_score = max(max_toxic_score, score)
            
            is_toxic = max_toxic_score > 0.18  # Very low threshold for stricter detection
            
            print(f"[CLIP] Max toxic score: {max_toxic_score:.3f}")
            if detected_labels:
                print(f"[CLIP] Detected: {detected_labels}")
            print(f"[CLIP] Result: {'✗ TOXIC' if is_toxic else '✓ SAFE'}")
            
            return is_toxic, detected_labels, toxic_scores
            
        except Exception as e:
            print(f"[CLIP] ❌ Error: {e}")
            return False, [], {}
    
    def analyze_with_zero_shot(self, image_description: str) -> Tuple[bool, List[str], Dict[str, float]]:
        """
        Use zero-shot classification on image description
        """
        if not self.zero_shot_classifier:
            return False, [], {}
        
        try:
            print(f"[ZERO-SHOT] Analyzing description: '{image_description[:50]}...'")
            
            # Categories to classify
            candidate_labels = [
                "cyberbullying",
                "harassment",
                "hate speech",
                "violence",
                "inappropriate",
                "safe content",
                "normal photo"
            ]
            
            result = self.zero_shot_classifier(
                image_description,
                candidate_labels=candidate_labels,
                multi_label=True
            )
            
            # Extract scores
            scores = {}
            detected_labels = []
            for label, score in zip(result['labels'], result['scores']):
                scores[label] = score
                if score > 0.5 and label != "safe content" and label != "normal photo":
                    detected_labels.append(label)
            
            is_toxic = len(detected_labels) > 0
            
            print(f"[ZERO-SHOT] Scores: {scores}")
            print(f"[ZERO-SHOT] Result: {'✗ TOXIC' if is_toxic else '✓ SAFE'}")
            
            return is_toxic, detected_labels, scores
            
        except Exception as e:
            print(f"[ZERO-SHOT] ❌ Error: {e}")
            return False, [], {}
    
    def analyze_image(self, image_path: str) -> Tuple[bool, List[str], Dict[str, float]]:
        """
        Main analysis function - combines all methods
        """
        print(f"\n[LOCAL ANALYZER] 🔍 Analyzing: {os.path.basename(image_path)}")
        
        all_labels = []
        all_scores = {}
        is_toxic = False
        
        # Method 1: CLIP analysis
        if self.clip_model:
            clip_toxic, clip_labels, clip_scores = self.analyze_with_clip(image_path)
            if clip_toxic:
                is_toxic = True
                all_labels.extend(clip_labels)
                all_scores.update(clip_scores)
        
        print(f"[LOCAL ANALYZER] Final result: {'✗ TOXIC' if is_toxic else '✓ SAFE'}\n")
        
        return is_toxic, list(set(all_labels)), all_scores
    
    def is_available(self) -> bool:
        """Check if any models are available"""
        return self.clip_model is not None or self.zero_shot_classifier is not None


# Global instance
_local_analyzer = None

def get_local_analyzer():
    """Get or create the global local analyzer instance"""
    global _local_analyzer
    if _local_analyzer is None:
        _local_analyzer = LocalImageAnalyzer()
    return _local_analyzer
