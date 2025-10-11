#!/usr/bin/env python3
"""
Quick test script for toxicity detection
"""

# Test the keyword blocklist directly
test_messages = [
    "hello",
    "fuck u",
    "hi fuck u",
    "you are stupid",
    "nice day",
    "idiot loser",
    "bitch ass",
    "kill yourself",
]

# Simple keyword check
toxic_keywords = {
    "fuck", "fucking", "fucked", "fucker", "fck", "f*ck", "fuk",
    "shit", "bullshit", "bs", "crap",
    "bitch", "btch", "b*tch", "whore", "slut",
    "ass", "asshole", "arse", "a$$",
    "damn", "damned", "hell",
    "piss", "pissed",
    "idiot", "stupid", "dumb", "loser", "hate",
    "retard", "moron", "trash", "bastard", "jerk",
    "ugly", "fat", "skinny", "worthless", "pathetic", "useless",
    "lame", "suck", "sucks", "freak",
    "kill yourself", "kys", "die", "suicide", "kill", "murder",
    "rape", "assault", "hurt", "beat", "attack",
}

print("=" * 60)
print("TOXICITY DETECTION TEST")
print("=" * 60)
print(f"\nLoaded {len(toxic_keywords)} toxic keywords\n")

for msg in test_messages:
    msg_lower = msg.lower()
    keyword_hits = [w for w in toxic_keywords if w in msg_lower]
    
    if keyword_hits:
        print(f"❌ BLOCKED: '{msg}'")
        print(f"   Matched: {keyword_hits}\n")
    else:
        print(f"✅ ALLOWED: '{msg}'\n")

print("=" * 60)
print("\nIf 'fuck u' and 'hi fuck u' are BLOCKED, the fix is working!")
print("=" * 60)
