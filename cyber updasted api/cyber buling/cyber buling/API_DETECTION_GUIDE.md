# 🔍 API DETECTION - COMPREHENSIVE LOGGING GUIDE

## ✅ ENHANCED LOGGING ADDED

I've added detailed logging throughout the entire detection system so you can see EXACTLY what's happening.

---

## 📊 STARTUP LOGS

When you run `python app.py`, you'll now see:

```
============================================================
🔧 TOXICITY DETECTION CONFIGURATION
============================================================
📊 Threshold: 0.5
🤖 Gemini API: ✅ ENABLED
   API Key: AIzaSyChilkmCmI4YiN9...IO6rNpc
🧠 Transformers (toxic-bert): ✅ Available
📚 Local Classifier: ✅ Loaded
🚫 Keyword Blocklist: 40 words
============================================================

[GEMINI] ✅ Initialized with API key: AIzaSyChilkmCmI4YiN9...IO6rNpc
[GROQ] ✅ Initialized with API key: gsk_Zs55vnSm9FSIMps0...Q48WHtAWOSXuk
[GROQ] Model: llama-3.1-70b-versatile, Bot: Grok Bot

============================================================
💬 CHAT BOT CONFIGURATION
============================================================
🤖 Groq API: ✅ ENABLED
   API Key: gsk_Zs55vnSm9FSIMps0...Q48WHtAWOSXuk
   Model: llama-3.1-70b-versatile
   Bot Name: Grok Bot
============================================================
```

---

## 🧪 TEXT MESSAGE DETECTION LOGS

### When you send a message like "fuck u":

```
[TOXICITY CHECK] Analyzing: 'fuck u'
[KEYWORD] ✗ TOXIC - Matched keywords: ['fuck']
```

**Result:** ❌ BLOCKED by keyword (instant)

---

### When you send "hello friend":

```
[TOXICITY CHECK] Analyzing: 'hello friend'
[KEYWORD] ✓ No toxic keywords found
[GEMINI] ⚠️  API disabled
[TRANSFORMERS] Checking with toxic-bert model...
[TRANSFORMERS] ✓ Text appears safe
[RESULT] ✓ Text is SAFE
```

**Result:** ✅ ALLOWED

---

### If Gemini IS enabled and detects toxicity:

```
[TOXICITY CHECK] Analyzing: 'you are worthless'
[KEYWORD] ✗ TOXIC - Matched keywords: ['worthless']
```

OR if keyword doesn't match:

```
[TOXICITY CHECK] Analyzing: 'subtle toxic message'
[KEYWORD] ✓ No toxic keywords found
[GEMINI TEXT] 🔍 Analyzing: 'subtle toxic message...'
[GEMINI] 📡 Sending request to API...
[GEMINI] 📥 Response status: 200
[GEMINI TEXT] 📊 Result: toxic=true, labels=['harassment'], scores={'harassment': 0.85}
[GEMINI TEXT] ✗ TOXIC
```

**Result:** ❌ BLOCKED by Gemini AI

---

## 🖼️ IMAGE UPLOAD DETECTION LOGS

### When you upload an image with toxic text:

```
[IMAGE MODERATION] Analyzing: uploads/abc123.jpg
[Gemini] Analyzing image with AI...
[GEMINI] 📡 Sending request to API...
[GEMINI] 📥 Response status: 200
[Gemini] ✗ TOXIC image detected: ['harassment', 'insult']
[OCR] Extracting text from image...
[OCR] Extracted text: 'STUPID IDIOT'
[OCR] ✗ TOXIC text detected: ['stupid', 'idiot']
[RESULT] is_toxic=True, labels=['harassment', 'insult', 'stupid', 'idiot']
```

**Result:** ❌ Image BLOCKED and deleted

---

### When you upload a clean image:

```
[IMAGE MODERATION] Analyzing: uploads/xyz789.jpg
[Gemini] Analyzing image with AI...
[GEMINI] 📡 Sending request to API...
[GEMINI] 📥 Response status: 200
[Gemini] ✓ Image appears safe
[OCR] Extracting text from image...
[OCR] Extracted text: ''
[OCR] No text found in image
[RESULT] is_toxic=False, labels=[]
```

**Result:** ✅ Image uploaded successfully

---

## 💬 GROQ BOT REPLY LOGS

### When bot generates a reply:

```
[GROQ] 💬 Generating reply for: 'hello...'
[GROQ] 📡 Sending request to API...
[GROQ] 📥 Response status: 200
[GROQ] ✅ Generated reply: 'Hello! How can I help you today?...'
```

**Result:** ✅ Bot reply sent

---

## 🚨 ERROR DETECTION LOGS

### If Gemini API key is invalid:

```
[GEMINI] ❌ Disabled - API key: Missing
```

OR

```
[GEMINI] 📡 Sending request to API...
[GEMINI] 📥 Response status: 403
[GEMINI] ❌ HTTP Error: 403 Client Error: Forbidden
[GEMINI] Response: {"error": {"code": 403, "message": "API key not valid"}}
```

---

### If Gemini API times out:

```
[GEMINI] 📡 Sending request to API...
[GEMINI] ⏱️  Timeout after 5s
[GEMINI TEXT] ❌ No response from API
```

---

### If Groq API fails:

```
[GROQ] 📡 Sending request to API...
[GROQ] 📥 Response status: 401
[GROQ] ❌ HTTP Error: 401 Client Error: Unauthorized
[GROQ] Response: {"error": {"message": "Invalid API key"}}
```

---

## 🔍 HOW TO DIAGNOSE ISSUES

### Issue 1: APIs not being called

**Check startup logs:**
```
🤖 Gemini API: ❌ DISABLED
```

**Solution:** Add to `.env`:
```
USE_GEMINI=true
USE_GROQ_BOT=true
```

---

### Issue 2: API key invalid

**Look for:**
```
[GEMINI] ❌ HTTP Error: 403
[GEMINI] Response: {"error": {"message": "API key not valid"}}
```

**Solution:** Verify API key in `.env` is correct

---

### Issue 3: Only keyword detection working

**Look for:**
```
[KEYWORD] ✗ TOXIC - Matched keywords: ['fuck']
```

**This is CORRECT!** Keyword detection is fastest and most reliable.
Gemini is only called if keyword doesn't match.

---

### Issue 4: Gemini not detecting anything

**Look for:**
```
[GEMINI TEXT] 📊 Result: toxic=false, labels=[], scores={}
```

**This means:** Gemini analyzed it but didn't find it toxic.
The keyword blocklist is more strict than Gemini.

---

## 📋 COMPLETE DETECTION FLOW

### Text Messages:

```
User sends message
    ↓
[TOXICITY CHECK] Analyzing: 'message'
    ↓
Layer 1: Keyword Blocklist
    ├─ Match found? → ❌ BLOCK (instant)
    └─ No match → Continue
    ↓
Layer 2: Gemini AI (if enabled)
    ├─ Toxic? → ❌ BLOCK
    └─ Safe? → Continue
    ↓
Layer 3: Transformers (toxic-bert)
    ├─ Toxic? → ❌ BLOCK
    └─ Safe? → ✅ ALLOW
```

---

### Images:

```
User uploads image
    ↓
[IMAGE MODERATION] Analyzing
    ↓
Layer 1: Gemini Vision AI
    ├─ Toxic? → ❌ BLOCK & DELETE
    └─ Safe? → Continue
    ↓
Layer 2: OCR Text Extraction
    ├─ Extract text
    ├─ Check keywords
    ├─ Toxic? → ❌ BLOCK & DELETE
    └─ Safe? → Continue
    ↓
Layer 3: Filename Check
    ├─ Toxic keyword in filename? → ❌ BLOCK & DELETE
    └─ Safe? → ✅ ALLOW
```

---

## ✅ WHAT TO LOOK FOR

### ✅ GOOD SIGNS:
```
[GEMINI] ✅ Initialized with API key: ...
[GROQ] ✅ Initialized with API key: ...
[GEMINI] 📡 Sending request to API...
[GEMINI] 📥 Response status: 200
[GROQ] 📡 Sending request to API...
[GROQ] 📥 Response status: 200
```

### ❌ BAD SIGNS:
```
[GEMINI] ❌ Disabled - API key: Missing
[GEMINI] ❌ HTTP Error: 403
[GEMINI] ⏱️  Timeout after 5s
[GROQ] ❌ HTTP Error: 401
```

---

## 🚀 TESTING STEPS

### 1. Start the app:
```bash
python app.py
```

### 2. Check startup logs:
- Look for "✅ ENABLED" for both Gemini and Groq
- Verify API keys are showing (partial)

### 3. Send test message: "fuck u"
**Expected logs:**
```
[TOXICITY CHECK] Analyzing: 'fuck u'
[KEYWORD] ✗ TOXIC - Matched keywords: ['fuck']
```

### 4. Send test message: "hello"
**Expected logs:**
```
[TOXICITY CHECK] Analyzing: 'hello'
[KEYWORD] ✓ No toxic keywords found
[GEMINI TEXT] 🔍 Analyzing: 'hello...'
[GEMINI] 📡 Sending request to API...
[GEMINI] 📥 Response status: 200
[GEMINI TEXT] ✓ SAFE
[GROQ] 💬 Generating reply for: 'hello...'
[GROQ] 📡 Sending request to API...
[GROQ] 📥 Response status: 200
[GROQ] ✅ Generated reply: ...
```

### 5. Upload toxic image
**Expected logs:**
```
[IMAGE MODERATION] Analyzing: ...
[Gemini] Analyzing image with AI...
[GEMINI] 📡 Sending request to API...
[GEMINI] 📥 Response status: 200
[Gemini] ✗ TOXIC image detected: ...
```

---

## 📝 SUMMARY

**Now you can see:**
- ✅ Which APIs are enabled/disabled
- ✅ When APIs are being called
- ✅ What responses APIs return
- ✅ Why messages are blocked/allowed
- ✅ Exact errors if APIs fail

**Just run the app and watch the console!**
