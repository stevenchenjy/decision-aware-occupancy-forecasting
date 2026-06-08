import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score


def empty_class_metrics(y_occupied, p_occupied, threshold=0.5):
    y_empty = 1 - np.asarray(y_occupied).ravel().astype(int)
    p_empty = np.clip(1.0 - np.asarray(p_occupied).ravel(), 1e-6, 1 - 1e-6)
    pred_empty = (p_empty >= threshold).astype(int)
    return {
        "positive_class": "Empty=1",
        "empty_auprc": average_precision_score(y_empty, p_empty),
        "empty_auroc": roc_auc_score(y_empty, p_empty) if len(np.unique(y_empty)) > 1 else np.nan,
        "empty_f1": f1_score(y_empty, pred_empty, zero_division=0),
        "empty_precision": precision_score(y_empty, pred_empty, zero_division=0),
        "empty_recall": recall_score(y_empty, pred_empty, zero_division=0),
        "empty_brier": brier_score_loss(y_empty, p_empty),
    }


def occupancy_conflict_rate(y_occupied, recommend_empty):
    y_occ = np.asarray(y_occupied).ravel().astype(int)
    rec = np.asarray(recommend_empty).ravel().astype(bool)
    fp = rec & (y_occ == 1)
    return fp.sum() / rec.sum() if rec.sum() else 0.0


def standard_fpr(y_occupied, recommend_empty):
    y_occ = np.asarray(y_occupied).ravel().astype(int)
    rec = np.asarray(recommend_empty).ravel().astype(bool)
    occupied = y_occ == 1
    return (rec & occupied).sum() / occupied.sum() if occupied.sum() else 0.0
