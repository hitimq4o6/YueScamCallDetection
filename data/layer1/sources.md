# Layer 1 sources

Checked 2026-10-15. Scores are advisory warnings, not legal determinations.

## Official whitelist

- 18222: Anti-Scam Helpline of the Anti-Deception Coordination Centre, Hong Kong Police. Verified at https://www.adcc.gov.hk/en-hk/contact-us.html
- #ADCC18222: ADCC registered SMS sender ID under OFCA SMS Sender Registration Scheme. Verified at https://www.adcc.gov.hk/en-hk/anti-deception-coordination-centre-to-enhance-scam-intervention-through-sms-communications.html
- 999: emergency number, stated on the same ADCC contact page.
- 34236611, 81056060, +852-1868: kept as official whitelist because the project list marks them official. Agency names were not confirmed on the ADCC pages checked. Labels are not invented.

## Keywords

- `scam_keywords_zh.csv` keeps the previous Chinese surfaces, remapped to `surface,lang,concept,weight`.
- A short extra set (轉帳, 保證金, 驗證碼, bank, warrant, and similar) comes from the project concept examples so combination scoring can run. These phrases still need a check against the ADCC handbook.
- `scam_keywords_en.csv` is a curated concept map from `kaggle_data/archive/English_Scam.txt` (400 English scam templates). Phrases were kept only when they did not appear in `English_NonScam.txt`. Ordinary words such as package, delivery, loan, and warranty were not added. This is conceptual mapping, not an official Hong Kong phrase list. On that pair, 400/400 non-scam texts scored low. Of the 400 scam templates, 109 scored high, 95 medium, and 196 low. The misses are mostly paraphrases or sales scripts that do not use these phrases.

## Not used

- `seed_blacklist.csv` is left empty. Community reports are not treated as an official blacklist.
- HKJunkCall was not scraped.

## Scoring limits

- Input is message text, not a separate caller-ID field.
- One concept cannot reach high alert. High alert needs at least two concepts, one of them high-weight.
- A whitelist number in the text heavily cuts the score. A scammer can mention 18222 to suppress a warning. Short codes 999 and 1868 only count as whitelist when they look like a hotline mention, so a price such as 999 does not wipe the score.
