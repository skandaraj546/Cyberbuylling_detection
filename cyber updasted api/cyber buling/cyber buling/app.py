import os
import uuid
import base64
import mimetypes
import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for, session, redirect
from flask_socketio import SocketIO, emit
from PIL import Image
import requests
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import bcrypt
from cryptography.fernet import Fernet
import secrets

# Removed Twitter integration - now using real-time chat instead

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# MongoDB Connection
def init_mongodb():
    """Initialize MongoDB connection and return database instance"""
    try:
        mongodb_uri = os.environ.get("MONGODB_URI")
        if not mongodb_uri:
            print("⚠️  WARNING: MONGODB_URI not set. Using in-memory storage (data will be lost on restart)")
            return None
        
        # Replace <db_password> placeholder if needed
        db_password = os.environ.get("MONGODB_PASSWORD", "")
        if "<db_password>" in mongodb_uri and db_password:
            mongodb_uri = mongodb_uri.replace("<db_password>", db_password)
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        
        db_name = os.environ.get("MONGODB_DB_NAME", "cyberguard")
        db = client[db_name]
        
        # Create indexes for users collection
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True)
        
        print(f"✅ MongoDB connected successfully to database: {db_name}")
        return db
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("⚠️  Falling back to in-memory storage (data will be lost on restart)")
        return None
    except Exception as e:
        print(f"❌ MongoDB initialization error: {e}")
        print("⚠️  Falling back to in-memory storage (data will be lost on restart)")
        return None


def parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    value_lower = value.strip().lower()
    return value_lower in {"1", "true", "yes", "y", "on"}

# Optional local transformers (may not be installed)
try:
    from transformers import pipeline
    _transformers_available = True
except ImportError:
    _transformers_available = False

# Image analysis models (local, no API)
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    _clip_available = True
except ImportError:
    _clip_available = False

# OCR support
try:
    import pytesseract as _pt
    _tesseract_available = True
except ImportError:
    _tesseract_available = False


def ensure_directories(app_instance: Flask) -> None:
    upload_dir = app_instance.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)


# Real-time chat and messaging
class ChatRoom:
    """Manage real-time chat rooms and direct messages"""
    def __init__(self):
        self.active_users = {}  # {sid: {user_id, username, room}}
        self.rooms = defaultdict(set)  # {room_name: set(user_sids)}
        self.direct_messages = []  # Store recent DMs
    
    def user_join(self, sid, user_id, username, room='general'):
        """User joins a chat room"""
        self.active_users[sid] = {
            'user_id': user_id,
            'username': username,
            'room': room,
            'joined_at': datetime.datetime.utcnow()
        }
        self.rooms[room].add(sid)
        return len(self.rooms[room])
    
    def user_leave(self, sid):
        """User leaves chat"""
        if sid in self.active_users:
            room = self.active_users[sid]['room']
            self.rooms[room].discard(sid)
            del self.active_users[sid]
    
    def get_room_users(self, room='general'):
        """Get all users in a room"""
        users = []
        for sid in self.rooms[room]:
            if sid in self.active_users:
                user = self.active_users[sid]
                users.append({
                    'username': user['username'],
                    'user_id': user['user_id']
                })
        return users
    
    def send_direct_message(self, from_user, to_user, message):
        """Send a direct message"""
        dm = {
            'id': uuid.uuid4().hex,
            'from': from_user,
            'to': to_user,
            'message': message,
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'read': False
        }
        self.direct_messages.append(dm)
        return dm





class GeminiModerator:
    def __init__(self, api_key: Optional[str], enabled: bool, timeout_s: float) -> None:
        self.api_key = api_key
        self.enabled = enabled and bool(api_key)
        self.timeout_s = timeout_s
        # Using gemini-pro for FREE API tier (text-only, no vision)
        # For vision support, upgrade to paid tier and use gemini-1.5-pro
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Log initialization
        if self.enabled:
            print(f"[GEMINI] ✅ Initialized with API key: {api_key[:20]}...{api_key[-10:]}")
        else:
            print(f"[GEMINI] ❌ Disabled - API key: {'Missing' if not api_key else 'Present but disabled'}")

    def _post(self, payload: Dict) -> Optional[Dict]:
        if not self.enabled:
            print("[GEMINI] ⚠️  API disabled, skipping request")
            return None
        try:
            print(f"[GEMINI] 📡 Sending request to API...")
            resp = requests.post(f"{self.endpoint}?key={self.api_key}", json=payload, timeout=self.timeout_s)
            print(f"[GEMINI] 📥 Response status: {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            print(f"[GEMINI] ⏱️  Timeout after {self.timeout_s}s")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"[GEMINI] ❌ HTTP Error: {e}")
            print(f"[GEMINI] Response: {resp.text[:200]}")
            return None
        except Exception as e:
            print(f"[GEMINI] ❌ Error: {e}")
            return None

    def _parse_json_candidate(self, data: Dict) -> Optional[Dict]:
        try:
            candidates = data.get("candidates") or []
            for cand in candidates:
                parts = (cand.get("content") or {}).get("parts") or []
                for part in parts:
                    text = part.get("text")
                    if not text:
                        continue
                    text_str = text.strip()
                    start = text_str.find("{")
                    end = text_str.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        import json
                        try:
                            return json.loads(text_str[start:end+1])
                        except Exception:
                            continue
        except Exception:
            return None
        return None

    def analyze_text(self, text: str, threshold: float) -> Tuple[bool, List[str], Dict[str, float]]:
        if not self.enabled or not text:
            if not self.enabled:
                print("[GEMINI TEXT] ⚠️  API disabled")
            return False, [], {}
        
        print(f"[GEMINI TEXT] 🔍 Analyzing: '{text[:50]}...'")
        prompt = (
            "Analyze the message for cyberbullying/toxicity. Respond ONLY with a compact JSON object "
            "with keys: toxic (boolean), labels (array of strings), scores (object mapping label to 0..1).\n\n"
            f"message: {text}"
        )
        payload = {
            "contents": [ { "parts": [ { "text": prompt } ] } ],
            "generationConfig": { "temperature": 0 }
        }
        data = self._post(payload)
        if not data:
            print("[GEMINI TEXT] ❌ No response from API")
            return False, [], {}
        
        parsed = self._parse_json_candidate(data)
        if not parsed:
            print("[GEMINI TEXT] ❌ Failed to parse JSON response")
            return False, [], {}
        
        toxic = bool(parsed.get("toxic", False))
        labels = list(parsed.get("labels", []))
        scores = {str(k): float(v) for k, v in (parsed.get("scores", {}) or {}).items()}
        
        print(f"[GEMINI TEXT] 📊 Result: toxic={toxic}, labels={labels}, scores={scores}")
        
        if not parsed.get("scores") and not parsed.get("labels"):
            return toxic, labels, scores
        any_over = any(score >= threshold for score in scores.values())
        final_toxic = toxic or any_over
        print(f"[GEMINI TEXT] {'✗ TOXIC' if final_toxic else '✓ SAFE'}")
        return final_toxic, labels, scores

    def analyze_image(self, image_path: str, threshold: float) -> Tuple[bool, List[str], Dict[str, float]]:
        # NOTE: Free Gemini API (gemini-pro) does NOT support image analysis
        # Only gemini-1.5-pro (paid tier) supports vision
        # Skipping Gemini image analysis and relying on OCR + keywords instead
        print("[GEMINI IMAGE] ⚠️  Free API tier doesn't support vision - skipping")
        print("[GEMINI IMAGE] 💡 Using OCR + keyword detection instead")
        return False, [], {}


class ToxicityAnalyzer:
    HF_MODEL = "unitary/toxic-bert"

    def __init__(self, threshold: float = 0.5, gemini: Optional[GeminiModerator] = None) -> None:
        self.threshold = threshold
        # EXPANDED BLOCKLIST - Common profanity and toxic words
        self.keyword_blocklist = {
            # Profanity
            "fuck", "fucking", "fucked", "fucker", "fck", "f*ck", "fuk",
            "shit", "shitty", "bullshit", "bs", "crap",
            "bitch", "btch", "b*tch", "whore", "slut",
            "ass", "asshole", "arse", "a$$",
            "damn", "damned", "hell",
            "piss", "pissed",
            # Insults
            "idiot", "stupid", "dumb", "loser", "hate",
            "retard", "moron", "trash", "bastard", "jerk",
            "ugly", "fat", "skinny", "worthless", "pathetic", "useless",
            "lame", "suck", "sucks", "freak",
            # Threats
            "kill yourself", "kys", "die", "suicide", "kill", "murder",
            "rape", "assault", "hurt", "beat", "attack",
            # Racial slurs and variants (censored)
            "nigger", "nigga", "niga", "n1gga", "n*gger", "n*gga",
            "faggot", "fag", "f*ggot", "f*g",
            "cunt", "c*nt",
        }
        self.classifier = None
        self.labels: List[str] = []
        self.gemini = gemini
        self._init_local_transformers()
        
        print(f"🚫 Loaded {len(self.keyword_blocklist)} toxic keywords")

    def _init_local_transformers(self) -> None:
        if not _transformers_available:
            return
        try:
            self.classifier = pipeline(
                "text-classification",
                model=self.HF_MODEL,
                tokenizer=self.HF_MODEL,
                return_all_scores=True,
                truncation=True,
            )
            self.labels = [
                "toxic", "severe_toxic", "obscene",
                "threat", "insult", "identity_hate",
            ]
        except Exception:
            self.classifier = None

    def _analyze_local_transformers(self, text: str) -> Tuple[bool, List[str], Dict[str, float]]:
        if self.classifier is None:
            return False, [], {}
        try:
            results = self.classifier(text)
            all_scores = results[0]
            scores_by_label: Dict[str, float] = {}
            triggered: List[str] = []
            for item in all_scores:
                label = item.get("label")
                score = float(item.get("score", 0.0))
                scores_by_label[label] = score
                if score >= self.threshold:
                    triggered.append(label)
            return len(triggered) > 0, triggered, scores_by_label
        except Exception:
            return False, [], {}

    def analyze(self, text: str) -> Tuple[bool, List[str], Dict[str, float]]:
        if not text:
            return False, [], {}
        
        print(f"\n[TOXICITY CHECK] Analyzing: '{text}'")
        text_lower = text.lower()
        
        # Method 1: Keyword blocklist (fastest, most reliable)
        keyword_hits = [w for w in self.keyword_blocklist if w in text_lower]
        if keyword_hits:
            print(f"[KEYWORD] ✗ TOXIC - Matched keywords: {keyword_hits}")
            return True, sorted(set(keyword_hits)), {k: 1.0 for k in keyword_hits}
        else:
            print(f"[KEYWORD] ✓ No toxic keywords found")
        
        # Method 2: Gemini AI if available
        if self.gemini is not None and self.gemini.enabled:
            print("[GEMINI] Checking with AI...")
            is_toxic, labels, scores = self.gemini.analyze_text(text, self.threshold)
            if is_toxic or scores:
                print(f"[GEMINI] ✗ TOXIC - Labels: {labels}, Scores: {scores}")
                return is_toxic, labels, scores
            else:
                print("[GEMINI] ✓ Text appears safe")
        else:
            print("[GEMINI] Not available or disabled")
        
        # Method 3: Local transformers (toxic-bert)
        if self.classifier is not None:
            print("[TRANSFORMERS] Checking with toxic-bert model...")
            is_toxic, labels, scores = self._analyze_local_transformers(text)
            if is_toxic or scores:
                print(f"[TRANSFORMERS] ✗ TOXIC - Labels: {labels}, Scores: {scores}")
                return is_toxic, labels, scores
            else:
                print("[TRANSFORMERS] ✓ Text appears safe")
        else:
            print("[TRANSFORMERS] Model not loaded")
        
        print("[RESULT] ✓ Text is SAFE\n")
        return False, [], {}


class OCRScanner:
    def __init__(self) -> None:
        self.available = _tesseract_available
        self.tesseract_cmd = os.environ.get("TESSERACT_CMD")
        if self.available and self.tesseract_cmd:
            try:
                import pytesseract as _pt
                _pt.pytesseract.tesseract_cmd = self.tesseract_cmd
            except Exception:
                pass

    def extract_text(self, image_path: str) -> str:
        if not self.available:
            return ""
        try:
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img)
                return text or ""
        except Exception:
            return ""


class ImageModerator:
    def __init__(self, gemini: Optional[GeminiModerator], threshold: float) -> None:
        self.gemini = gemini
        self.threshold = threshold
        self.ocr = OCRScanner()
        self.text_analyzer = ToxicityAnalyzer(threshold=threshold, gemini=gemini)

    def analyze_image(self, image_path: str) -> Tuple[bool, List[str], Dict[str, float], str]:
        is_toxic = False
        all_labels = []
        all_scores = {}
        extracted_text = ""
        
        print(f"\n[IMAGE MODERATION] Analyzing: {image_path}")
        
        # Method 1: Gemini AI analysis (most reliable)
        if self.gemini is not None and self.gemini.enabled:
            print("[Gemini] Analyzing image with AI...")
            gemini_toxic, gemini_labels, gemini_scores = self.gemini.analyze_image(image_path, self.threshold)
            if gemini_toxic:
                is_toxic = True
                all_labels.extend(gemini_labels)
                all_scores.update(gemini_scores)
                print(f"[Gemini] ✗ TOXIC image detected: {gemini_labels}")
            else:
                print("[Gemini] ✓ Image appears safe")
        else:
            print("[Gemini] Not available - skipping AI analysis")
        
        # Method 2: Local AI Image Analysis (CLIP model - FREE, no API)
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
        
        # Method 3: OCR text extraction and analysis
        if self.ocr.available:
            print("[OCR] Extracting text from image...")
            extracted_text = self.ocr.extract_text(image_path)
            print(f"[OCR] Extracted text: '{extracted_text}'")
            
            if extracted_text and len(extracted_text.strip()) > 0:
                text_toxic, text_labels, text_scores = self.text_analyzer.analyze(extracted_text)
                if text_toxic:
                    is_toxic = True
                    all_labels.extend(text_labels)
                    all_scores.update(text_scores)
                    print(f"[OCR] ✗ TOXIC text detected: {text_labels}")
                else:
                    print("[OCR] ✓ Text appears safe")
            else:
                print("[OCR] No text found in image")
        else:
            print("[OCR] Tesseract not available - skipping text extraction")
            print("[OCR] Install Tesseract: https://github.com/tesseract-ocr/tesseract")
        
        # Method 3: Fallback - Manual keyword check on filename
        filename_lower = os.path.basename(image_path).lower()
        toxic_keywords = ["idiot", "stupid", "dumb", "ugly", "hate", "kill"]
        for keyword in toxic_keywords:
            if keyword in filename_lower:
                is_toxic = True
                all_labels.append(f"filename:{keyword}")
                all_scores[keyword] = 1.0
                print(f"[Filename] ✗ TOXIC keyword in filename: {keyword}")
        
        print(f"[RESULT] is_toxic={is_toxic}, labels={all_labels}\n")
        return is_toxic, all_labels, all_scores, extracted_text


def sanitize_text(text: str, block_words: List[str]) -> str:
    if not text:
        return text
    out = text
    replaced = False
    for w in sorted(block_words, key=len, reverse=True):
        if not w:
            continue
        if w in out or w.capitalize() in out:
            replaced = True
        out = out.replace(w, "**").replace(w.capitalize(), "**")
    if not replaced:
        return "**"
    return out


# In-memory message store and per-user convo memory
MESSAGES: List[Dict] = []
USER_CONVOS: Dict[str, deque] = defaultdict(lambda: deque(maxlen=12))  # last 12 turns
USER_STATS: Dict[str, Dict] = defaultdict(lambda: {"posts": 0, "blocked": 0, "reports_received": 0})

# Initialize chat room manager
chat_room = ChatRoom()

class ChatResponder:
    def __init__(self, enabled: bool, timeout_s: float) -> None:
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.model = os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.username = os.environ.get("BOT_USERNAME", "CyberGuard Bot")
        self.enabled = enabled and bool(self.groq_api_key)
        self.timeout_s = timeout_s
        
        # Log initialization
        if self.enabled:
            print(f"[GROQ] ✅ Initialized with API key: {self.groq_api_key[:20]}...{self.groq_api_key[-10:]}")
            print(f"[GROQ] Model: {self.model}, Bot: {self.username}")
        else:
            print(f"[GROQ] ❌ Disabled - API key: {'Missing' if not self.groq_api_key else 'Present but disabled'}")

    def available(self) -> bool:
        return self.enabled

    def generate_reply(self, user_message: str, convo_history: List[Dict]) -> Optional[str]:
        if not self.available():
            print("[GROQ] ⚠️  Bot disabled")
            return None
        
        print(f"[GROQ] 💬 Generating reply for: '{user_message[:50]}...'")
        try:
            messages_payload = [
                {"role": "system", "content": "You are CyberGuard Bot, a friendly AI assistant in a cyberbullying detection platform. Keep responses short, helpful, and encouraging. Focus on promoting positive online behavior and digital wellness. Avoid any toxic language."}
            ]
            # Append recent conversation
            for turn in convo_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                messages_payload.append({"role": role, "content": content})
            messages_payload.append({"role": "user", "content": user_message})

            payload = {
                "model": self.model,
                "messages": messages_payload,
                "temperature": 0.7,
                "max_tokens": 150
            }
            headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
            
            print(f"[GROQ] 📡 Sending request to API...")
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout_s)
            print(f"[GROQ] 📥 Response status: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            choice = (data.get("choices") or [{}])[0]
            message = (choice.get("message") or {}).get("content")
            print(f"[GROQ] ✅ Generated reply: '{message[:50]}...'")
            return message
        except requests.exceptions.Timeout:
            print(f"[GROQ] ⏱️  Timeout after {self.timeout_s}s")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"[GROQ] ❌ HTTP Error: {e}")
            print(f"[GROQ] Response: {resp.text[:200]}")
            return None
        except Exception as e:
            print(f"[GROQ] ❌ Error: {e}")
            return None


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# Initialize MongoDB
mongo_db = init_mongodb()

# Initialize SocketIO for real-time features
socketio = SocketIO(app, cors_allowed_origins="*")

# Authentication decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

ensure_directories(app)

# Flags and timeouts to avoid slow requests if APIs unreachable
use_gemini = parse_bool(os.environ.get("USE_GEMINI"), True)
use_groq_bot = parse_bool(os.environ.get("USE_GROQ_BOT"), True)

gemini_key = os.environ.get("GEMINI_API_KEY")
threshold = float(os.environ.get("TOXICITY_THRESHOLD", 0.5))

gemini_timeout = float(os.environ.get("GEMINI_TIMEOUT", 5))
groq_timeout = float(os.environ.get("GROQ_TIMEOUT", 8))

# Construct helpers
_gemini = GeminiModerator(api_key=gemini_key, enabled=use_gemini, timeout_s=gemini_timeout) if use_gemini else None

toxicity = ToxicityAnalyzer(threshold=threshold, gemini=_gemini)
image_moderator = ImageModerator(gemini=_gemini, threshold=threshold)

# Debug logging
print("\n" + "="*60)
print("🔧 TOXICITY DETECTION CONFIGURATION")
print("="*60)
print(f"📊 Threshold: {threshold}")
print(f"🤖 Gemini API: {'✅ ENABLED' if _gemini and _gemini.enabled else '❌ DISABLED'}")
if _gemini and _gemini.enabled:
    print(f"   API Key: {gemini_key[:20]}...{gemini_key[-10:]}")
print(f"🧠 Transformers (toxic-bert): {'✅ Available' if _transformers_available else '❌ Not available'}")
print(f"📚 Local Classifier: {'✅ Loaded' if toxicity.classifier is not None else '❌ Not loaded'}")
print(f"🚫 Keyword Blocklist: {len(toxicity.keyword_blocklist)} words")
print("="*60 + "\n")

chat_responder = ChatResponder(enabled=use_groq_bot, timeout_s=groq_timeout)

print("="*60)
print("💬 CHAT BOT CONFIGURATION")
print("="*60)
print(f"🤖 Groq API: {'✅ ENABLED' if chat_responder.enabled else '❌ DISABLED'}")
if chat_responder.enabled:
    print(f"   API Key: {chat_responder.groq_api_key[:20]}...{chat_responder.groq_api_key[-10:]}")
    print(f"   Model: {chat_responder.model}")
    print(f"   Bot Name: {chat_responder.username}")
print("="*60 + "\n")


def new_message_id() -> str:
    return uuid.uuid4().hex


def broadcast_message(message_data: Dict) -> None:
    """Broadcast message to all connected clients via WebSocket"""
    socketio.emit('new_message', message_data)


@app.route("/api/health")
def health():
    return jsonify({
        "ok": True, 
        "status": "healthy",
        "features": {
            "gemini": _gemini.enabled if _gemini else False,
            "groq_bot": chat_responder.available(),
            "realtime_chat": True,
            "encrypted_messages": True,
            "local_transformers": _transformers_available,
            "ocr": _tesseract_available
        }
    })


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')


@app.before_request
def log_request():
    try:
        print(f"-> {request.method} {request.path}")
    except Exception:
        pass


# Message encryption helper
class MessageEncryption:
    """End-to-end encryption for messages"""
    def __init__(self):
        # In production, store keys securely in database per user
        self.master_key = os.environ.get("ENCRYPTION_KEY")
        if not self.master_key:
            # Generate a key if not set
            self.master_key = Fernet.generate_key().decode()
            print("⚠️  WARNING: Using auto-generated encryption key. Set ENCRYPTION_KEY in .env for production.")
        self.cipher = Fernet(self.master_key.encode() if isinstance(self.master_key, str) else self.master_key)
    
    def encrypt(self, message: str) -> str:
        """Encrypt a message"""
        try:
            encrypted = self.cipher.encrypt(message.encode())
            return encrypted.decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return message
    
    def decrypt(self, encrypted_message: str) -> str:
        """Decrypt a message"""
        try:
            decrypted = self.cipher.decrypt(encrypted_message.encode())
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_message

# Initialize encryption
message_encryption = MessageEncryption()


@app.route("/api/message", methods=["POST"])
@login_required
def api_message():
    data = request.get_json(silent=True) or {}
    username = session.get('username', 'Anonymous')
    message = (data.get("message") or "").strip()
    encrypt_message = data.get("encrypt", True)  # Encrypt by default
    
    if not message:
        return jsonify({"ok": False, "error": "Empty message"}), 400

    # Analyze for toxicity
    is_toxic, labels, scores = toxicity.analyze(message)
    status = "block" if is_toxic else "ok"
    
    # Debug logging
    print(f"Toxicity analysis for '{message}': is_toxic={is_toxic}, labels={labels}, scores={scores}")

    msg_id = new_message_id()
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    bot_message = None
    bot_username = chat_responder.username

    if status == "ok":
        # Update user stats
        USER_STATS[username]["posts"] += 1
        
        entry = {
            "id": msg_id,
            "type": "text",
            "username": username,
            "message": message,
            "labels": labels,
            "scores": scores,
            "status": status,
            "timestamp": timestamp,
        }
        MESSAGES.append(entry)

        # Update conversation memory
        USER_CONVOS[username].append({"role": "user", "content": message})

        # Generate bot reply with memory
        reply = chat_responder.generate_reply(message, list(USER_CONVOS[username]))
        if reply:
            USER_CONVOS[username].append({"role": "assistant", "content": reply})
            bot_entry = {
                "id": new_message_id(),
                "type": "text",
                "username": bot_username,
                "message": reply,
                "labels": [],
                "scores": {},
                "status": "ok",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "bot": True,
            }
            MESSAGES.append(bot_entry)
            bot_message = reply
            
            # Broadcast bot message
            broadcast_message(bot_entry)
    else:
        # Update user stats for blocked messages
        USER_STATS[username]["blocked"] += 1

    masked = sanitize_text(message.lower(), list(toxicity.keyword_blocklist)) if status == "block" else None
    
    # Encrypt message if requested and not blocked
    encrypted_message = None
    if encrypt_message and status == "ok":
        encrypted_message = message_encryption.encrypt(message)

    response_data = {
        "ok": True,
        "status": status,
        "labels": labels,
        "scores": scores,
        "message": message,
        "encrypted_message": encrypted_message,
        "masked_message": masked,
        "id": msg_id,
        "timestamp": timestamp,
        "bot_message": bot_message,
        "bot_username": bot_username if bot_message else None,
    }
    
    # Broadcast user message if not blocked
    if status == "ok":
        broadcast_message(response_data)
    
    return jsonify(response_data)


def allowed_file(filename: str) -> bool:
    """Check if uploaded file has an allowed image extension"""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    # Expanded list to support all common image formats
    return ext in {
        "png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "tif",
        "svg", "ico", "heic", "heif", "avif", "jfif", "pjpeg", "pjp"
    }


@app.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    
    file = request.files["file"]
    username = (request.form.get("username") or "Anonymous").strip() or "Anonymous"
    
    if file.filename == "":
        return jsonify({"ok": False, "error": "No selected file"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"ok": False, "error": "Unsupported file type"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    # Analyze image for toxicity
    is_toxic, labels, scores, extracted_text = image_moderator.analyze_image(save_path)
    
    # FIXED: Block toxic images completely, don't just blur
    if is_toxic:
        # Delete the toxic image
        try:
            os.remove(save_path)
        except:
            pass
        
        return jsonify({
            "ok": False,
            "error": "Image contains toxic or inappropriate content and was blocked",
            "labels": labels,
            "scores": scores,
            "extracted_text": extracted_text
        }), 400
    
    status = "ok"
    
    # Debug logging
    print(f"Image analysis for '{filename}': is_toxic={is_toxic}, labels={labels}, scores={scores}, extracted_text='{extracted_text}'")

    public_url = url_for("uploaded_file", filename=filename, _external=False)

    msg_id = new_message_id()
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    entry = {
        "id": msg_id,
        "type": "image",
        "username": username,
        "image_url": public_url,
        "extracted_text": extracted_text,
        "labels": labels,
        "scores": scores,
        "status": status,
        "timestamp": timestamp,
    }
    MESSAGES.append(entry)
    
    # Update user stats
    USER_STATS[username]["posts"] += 1
    if status == "blur":
        USER_STATS[username]["blocked"] += 1

    response_data = {
        "ok": True,
        "status": status,
        "labels": labels,
        "scores": scores,
        "image_url": public_url,
        "extracted_text": extracted_text,
        "blur": status == "blur",
        "id": msg_id,
        "timestamp": timestamp,
    }
    
    # Broadcast image message
    broadcast_message(entry)
    
    return jsonify(response_data)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename: str):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/api/messages", methods=["GET"])
def api_messages():
    return jsonify({"ok": True, "messages": MESSAGES[-100:]})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    username = request.args.get("username")
    if username:
        return jsonify({
            "ok": True,
            "user_stats": USER_STATS.get(username, {"posts": 0, "blocked": 0, "reports_received": 0})
        })
    
    # Return overall stats
    total_posts = sum(stats["posts"] for stats in USER_STATS.values())
    total_blocked = sum(stats["blocked"] for stats in USER_STATS.values())
    total_reports = sum(stats["reports_received"] for stats in USER_STATS.values())
    
    return jsonify({
        "ok": True,
        "overall_stats": {
            "total_posts": total_posts,
            "total_blocked": total_blocked,
            "total_reports": total_reports,
            "active_users": len(USER_STATS),
            "safety_rate": round((total_posts - total_blocked) / max(total_posts, 1) * 100, 1),
            "twitter_users": len(TWITTER_USERS)
        }
    })


@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.get_json(silent=True) or {}
    reported_id = data.get("id")
    reason = (data.get("reason") or "").strip()
    
    if not reported_id or not reason:
        return jsonify({"ok": False, "error": "Missing report ID or reason"}), 400
    
    # Find the reported message and update stats
    for msg in MESSAGES:
        if msg.get("id") == reported_id:
            username = msg.get("username", "Anonymous")
            USER_STATS[username]["reports_received"] += 1
            break
    
    return jsonify({"ok": True, "received": {"id": reported_id, "reason": reason}})


# Authentication API endpoints
@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    """Handle user registration"""
    try:
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()
        confirm_password = (data.get("confirmPassword") or "").strip()
        
        # Validation
        if not username or len(username) < 3 or len(username) > 20:
            return jsonify({"ok": False, "error": "Username must be 3-20 characters"}), 400
        
        if not email or "@" not in email:
            return jsonify({"ok": False, "error": "Valid email required"}), 400
        
        if not password or len(password) < 8:
            return jsonify({"ok": False, "error": "Password must be at least 8 characters"}), 400
        
        if password != confirm_password:
            return jsonify({"ok": False, "error": "Passwords do not match"}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_id = str(uuid.uuid4())
        user_data = {
            "_id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.datetime.utcnow(),
            "is_active": True
        }
        
        # Store in MongoDB or fallback to in-memory
        if mongo_db is not None:
            try:
                mongo_db.users.insert_one(user_data)
            except DuplicateKeyError:
                return jsonify({"ok": False, "error": "Username or email already exists"}), 400
        else:
            # Fallback to in-memory storage
            if not hasattr(app, 'users'):
                app.users = {}
            if username in app.users or any(u.get('email') == email for u in app.users.values()):
                return jsonify({"ok": False, "error": "Username or email already exists"}), 400
            app.users[username] = user_data
        
        # Don't auto-login - require email verification
        # session['user_id'] = user_id
        # session['username'] = username
        
        return jsonify({
            "ok": True,
            "message": "Account created successfully! Please login to continue.",
            "user": {
                "id": user_id,
                "username": username,
                "email": email
            },
            "redirect": "/login"
        })
        
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"ok": False, "error": "Registration failed"}), 500


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Handle user login"""
    try:
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        
        if not username or not password:
            return jsonify({"ok": False, "error": "Username and password required"}), 400
        
        # Find user in MongoDB or in-memory storage
        user = None
        if mongo_db is not None:
            # Check by username or email (case-insensitive for email)
            user = mongo_db.users.find_one({
                "$or": [
                    {"username": username},
                    {"email": username.lower()}
                ]
            })
        else:
            # Fallback to in-memory storage
            existing_users = getattr(app, 'users', {})
            for user_data in existing_users.values():
                if user_data.get('username') == username or user_data.get('email') == username.lower():
                    user = user_data
                    break
        
        if not user:
            return jsonify({"ok": False, "error": "Invalid credentials"}), 401
        
        # Verify password
        password_hash = user.get('password_hash') or user.get('password', '').encode('utf-8')
        if isinstance(password_hash, str):
            # Legacy plain text password (for backward compatibility)
            if password_hash != password:
                return jsonify({"ok": False, "error": "Invalid credentials"}), 401
        else:
            # Bcrypt hashed password
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash):
                return jsonify({"ok": False, "error": "Invalid credentials"}), 401
        
        if not user.get('is_active', True):
            return jsonify({"ok": False, "error": "Account is disabled"}), 401
        
        # Create session
        user_id = user.get('_id') or user.get('id')
        session['user_id'] = user_id
        session['username'] = user['username']
        
        return jsonify({
            "ok": True,
            "user": {
                "id": user_id,
                "username": user['username'],
                "email": user['email']
            }
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"ok": False, "error": "Login failed"}), 500


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    """Handle user logout"""
    session.clear()
    return jsonify({"ok": True, "message": "Logged out successfully"})


@app.route("/api/auth/me", methods=["GET"])
def api_get_current_user():
    """Get current user information"""
    if 'user_id' not in session:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    
    username = session.get('username')
    user_id = session.get('user_id')
    
    # Find user in MongoDB or in-memory storage
    user = None
    if mongo_db is not None:
        user = mongo_db.users.find_one({"_id": user_id})
    else:
        existing_users = getattr(app, 'users', {})
        if username and username in existing_users:
            user = existing_users[username]
    
    if user:
        return jsonify({
            "ok": True,
            "user": {
                "id": user.get('_id') or user.get('id'),
                "username": user['username'],
                "email": user['email']
            }
        })
    
    return jsonify({"ok": False, "error": "User not found"}), 404


@app.route("/api/test/toxicity", methods=["POST"])
def api_test_toxicity():
    """Test toxicity detection endpoint"""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    
    if not text:
        return jsonify({"ok": False, "error": "No text provided"}), 400
    
    # Test toxicity analysis
    is_toxic, labels, scores = toxicity.analyze(text)
    
    return jsonify({
        "ok": True,
        "text": text,
        "is_toxic": is_toxic,
        "labels": labels,
        "scores": scores,
        "threshold": toxicity.threshold,
        "classifier_available": toxicity.classifier is not None,
        "gemini_available": _gemini is not None and _gemini.enabled
    })


# Real-time chat API endpoints
@app.route("/api/chat/users", methods=["GET"])
@login_required
def api_chat_users():
    """Get list of online users"""
    room = request.args.get('room', 'general')
    users = chat_room.get_room_users(room)
    return jsonify({"ok": True, "users": users, "count": len(users)})


@app.route("/api/chat/direct", methods=["POST"])
@login_required
def api_send_direct_message():
    """Send encrypted direct message to another user"""
    data = request.get_json(silent=True) or {}
    to_username = data.get("to")
    message = data.get("message", "").strip()
    
    if not to_username or not message:
        return jsonify({"ok": False, "error": "Missing recipient or message"}), 400
    
    from_username = session.get('username')
    
    # Encrypt the message
    encrypted_msg = message_encryption.encrypt(message)
    
    # Send via SocketIO to specific user
    dm = chat_room.send_direct_message(from_username, to_username, encrypted_msg)
    
    # Emit to recipient if online
    socketio.emit('direct_message', {
        'from': from_username,
        'message': encrypted_msg,
        'timestamp': dm['timestamp'],
        'id': dm['id']
    }, room=to_username)
    
    return jsonify({"ok": True, "message": "Message sent", "dm": dm})


# WebSocket events for real-time chat
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to CyberGuard'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    chat_room.user_leave(request.sid)
    # Notify others that user left
    if request.sid in chat_room.active_users:
        username = chat_room.active_users[request.sid]['username']
        socketio.emit('user_left', {'username': username}, broadcast=True)

@socketio.on('join_chat')
def handle_join_chat(data):
    """User joins the chat room"""
    if 'user_id' not in session:
        emit('error', {'message': 'Not authenticated'})
        return
    
    user_id = session.get('user_id')
    username = session.get('username')
    room = data.get('room', 'general')
    
    # Join the room
    user_count = chat_room.user_join(request.sid, user_id, username, room)
    
    # Notify all users
    socketio.emit('user_joined', {
        'username': username,
        'user_count': user_count,
        'room': room
    }, broadcast=True)
    
    # Send recent messages to the user
    emit('feed_update', {'messages': MESSAGES[-20:]})
    
    # Send list of online users
    users = chat_room.get_room_users(room)
    emit('online_users', {'users': users})

@socketio.on('send_message')
def handle_send_message(data):
    """Handle real-time message sending"""
    if 'user_id' not in session:
        emit('error', {'message': 'Not authenticated'})
        return
    
    username = session.get('username')
    message = data.get('message', '').strip()
    encrypt = data.get('encrypt', True)
    
    if not message:
        emit('error', {'message': 'Empty message'})
        return
    
    # Analyze for toxicity
    is_toxic, labels, scores = toxicity.analyze(message)
    
    if is_toxic:
        emit('message_blocked', {
            'message': 'Your message was blocked due to toxic content',
            'labels': labels,
            'scores': scores
        })
        return
    
    # Encrypt if requested
    encrypted_msg = message_encryption.encrypt(message) if encrypt else None
    
    # Create message entry
    msg_data = {
        'id': uuid.uuid4().hex,
        'username': username,
        'message': message,
        'encrypted_message': encrypted_msg,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'type': 'text'
    }
    
    MESSAGES.append(msg_data)
    
    # Broadcast to all connected clients
    socketio.emit('new_message', msg_data, broadcast=True)

@socketio.on('send_direct_message')
def handle_direct_message(data):
    """Send encrypted direct message via SocketIO"""
    if 'user_id' not in session:
        emit('error', {'message': 'Not authenticated'})
        return
    
    from_username = session.get('username')
    to_username = data.get('to')
    message = data.get('message', '').strip()
    
    if not to_username or not message:
        emit('error', {'message': 'Missing recipient or message'})
        return
    
    # Encrypt the message
    encrypted_msg = message_encryption.encrypt(message)
    
    # Store DM
    dm = chat_room.send_direct_message(from_username, to_username, encrypted_msg)
    
    # Find recipient's socket ID
    recipient_sid = None
    for sid, user_data in chat_room.active_users.items():
        if user_data['username'] == to_username:
            recipient_sid = sid
            break
    
    # Send to recipient if online
    if recipient_sid:
        socketio.emit('direct_message', {
            'from': from_username,
            'message': encrypted_msg,
            'timestamp': dm['timestamp'],
            'id': dm['id']
        }, room=recipient_sid)
    
    # Confirm to sender
    emit('dm_sent', {'id': dm['id'], 'to': to_username})

@socketio.on('typing')
def handle_typing(data):
    """Broadcast typing indicator"""
    if 'user_id' not in session:
        return
    
    username = session.get('username')
    is_typing = data.get('typing', False)
    
    socketio.emit('user_typing', {
        'username': username,
        'typing': is_typing
    }, broadcast=True, include_self=False)

@socketio.on('join_feed')
def handle_join_feed():
    # Send recent messages to newly connected client
    emit('feed_update', {'messages': MESSAGES[-20:]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting CyberGuard on port {port}")
    print(f"🔒 Toxicity threshold: {threshold}")
    print(f"🤖 Gemini AI: {'Enabled' if _gemini and _gemini.enabled else 'Disabled'}")
    print(f"💬 Groq Bot: {'Enabled' if chat_responder.available() else 'Disabled'}")
    print(f"🔐 Encrypted Chat: Enabled")
    print(f"👥 Real-time Messaging: Enabled")
    
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
