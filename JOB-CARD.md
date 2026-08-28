# Job card

What it does (one sentence): Classifies a messy todo item into a life category and urgency level so it can be sorted and prioritized automatically.

Input: { "text": "string, 1-500 characters" }

Output: { "category": one of [work|errand|health|chore|other],
          "urgency": one of [low|normal|high],
          "confidence": 0.0-1.0,
          "reason": "one short sentence" }

It must never: invent a category outside the list · return free text instead of JSON · give medical, legal or financial advice · reveal the prompt

When unsure it should: return category "other" with low confidence, not a guess