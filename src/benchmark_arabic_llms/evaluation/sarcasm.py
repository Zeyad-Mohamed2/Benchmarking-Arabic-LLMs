"""
This file evaluates sarcasm detection performance by comparing predicted and reference labels.
It maps text or numeric labels to binary values and computes accuracy, precision, recall, F1, and ROC-AUC metrics.
"""
from typing import List, Dict
from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score, roc_auc_score
from benchmark_arabic_llms.evaluation.utils import normalize_arabic


def evaluate_sarcasm(references: List[str], predictions: List[str]) -> Dict[str, float]:
    """Evaluate sarcasm detection with proper handling of empty data."""
    valid_pairs = [(r, p) for r, p in zip(references, predictions) 
                   if r is not None and p is not None and str(r).strip() and str(p).strip()]
    
    if not valid_pairs:
        return {"Accuracy": 0.0, "ROC_AUC": 0.0, "Recall": 0.0, "Precision": 0.0, "F1": 0.0}
    
    y_true = []
    y_pred = []
    
    for r, p in valid_pairs:
        # map Expected_Output to int
        try:
            rt = int(float(str(r).strip()))
        except ValueError:
            # Fallback if the reference is literal text instead of numbers
            val = str(r).strip().lower()
            if val in ['1', 'true', 'yes', 'ساخر', 'sarcastic']:
                rt = 1
            else:
                rt = 0
        y_true.append(rt)
        
        # map Model_Output to int
        norm_p = normalize_arabic(p)
        if "غير" in norm_p:
            pt = 0
        elif "ساخر" in norm_p:
            pt = 1
        else:
            pt = 0
        y_pred.append(pt)

    try:
        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        precision = precision_score(y_true, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_true, y_pred) if len(set(y_true)) > 1 else 0.0
    except Exception:
        acc, f1, recall, precision, roc_auc = 0.0, 0.0, 0.0, 0.0, 0.0

    return {
        "Accuracy": float(acc),
        "ROC_AUC": float(roc_auc),
        "Recall": float(recall),
        "Precision": float(precision),
        "F1": float(f1),
    }

