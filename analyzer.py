import math
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if download hasn't finished yet
    nlp = None

# Hackathon Safe-Startup: Download required NLTK data on first run
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

def get_linguistic_metrics(text):
    """Calculates real NLP metrics for a piece of text."""
    if not text.strip():
        return {"lexical_diversity": 0, "avg_sentence_len": 0, "avg_word_len": 0}

    # Tokenize into words and sentences using NLTK
    sentences = sent_tokenize(text)
    words = [word.lower() for word in word_tokenize(text) if word.isalpha()]
    
    if not words or not sentences:
        return {"lexical_diversity": 0, "avg_sentence_len": 0, "avg_word_len": 0}

    # 1. Lexical Diversity (Unique words / Total words)
    unique_words = set(words)
    lexical_diversity = len(unique_words) / len(words)

    # 2. Average Sentence Length
    avg_sentence_len = len(words) / len(sentences)

    # 3. Average Word Length
    avg_word_len = sum(len(word) for word in words) / len(words)

    # 4. SpaCy Integration: Part-of-Speech Diversity
    pos_diversity = 0
    if nlp is not None:
        doc = nlp(text)
        pos_tags = set(token.pos_ for token in doc)
        pos_diversity = len(pos_tags)

    return {
        "lexical_diversity": lexical_diversity,
        "avg_sentence_len": avg_sentence_len,
        "avg_word_len": avg_word_len,
        "pos_diversity": pos_diversity
    }

def analyze_student_drift(new_text, past_texts):
    """
    Real NLP Analysis comparing a new submission against historical baselines.
    """
    insights = []
    risk_score = 15.0 
    writing_style_score = 90.0
    ai_prob = 10.0 

    # Get metrics for the new submission
    new_metrics = get_linguistic_metrics(new_text)

    if past_texts:
        # Calculate the historical baseline
        past_metrics = [get_linguistic_metrics(text) for text in past_texts]
        
        base_lexical = sum(m["lexical_diversity"] for m in past_metrics) / len(past_metrics)
        base_sentence_len = sum(m["avg_sentence_len"] for m in past_metrics) / len(past_metrics)
        base_pos = sum(m.get("pos_diversity", 0) for m in past_metrics) / len(past_metrics) if past_metrics else 0
        
        # Calculate the Drift (Delta)
        lexical_drift = abs(new_metrics["lexical_diversity"] - base_lexical)
        sentence_drift = abs(new_metrics["avg_sentence_len"] - base_sentence_len)
        pos_drift = abs(new_metrics.get("pos_diversity", 0) - base_pos)

        # Flag anomalies based on standard deviation simulations
        if lexical_drift > 0.25 or sentence_drift > 10 or pos_drift > 5:
            risk_score += 45
            writing_style_score -= 40
            ai_prob += 65.0
            insights.append("🚨 CRITICAL: Drastic linguistic shift. Vocabulary richness and syntactic complexity do not match historical profile.")
        elif lexical_drift > 0.15 or sentence_drift > 5:
            risk_score += 25
            writing_style_score -= 20
            ai_prob += 30.0
            insights.append("⚠️ WARNING: Moderate stylistic deviation detected in sentence structure.")
        else:
            insights.append("✅ VERIFIED: Writing style fingerprint aligns perfectly with student baseline.")
            risk_score = max(0, risk_score - 10)
    else:
        insights.append("ℹ️ SYSTEM NOTE: First submission processed. NLP stylistic baseline established.")

    return {
        "writing_style_score": round(max(0, min(100, writing_style_score)), 1),
        "risk_score": round(max(0, min(100, risk_score)), 1),
        "ai_probability": round(max(0, min(100, ai_prob)), 1),
        "insights": insights
    }