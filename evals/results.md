# Eval Results

Date: 2026-08-30
Prompt version: triage-v1
Model: minimax/minimax-m2.7:free

Score: 7/8 on category

Failed case: "book dentist appointment for next week" — expected `health`, got `errand`.
This is a genuinely ambiguous case: a dentist visit is both a health matter and a scheduling task. The model's answer is defensible, not clearly wrong.