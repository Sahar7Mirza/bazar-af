"""Survey analytics: descriptives, Cronbach's alpha, correlations, OLS regression.
Pure functions over a pandas DataFrame so they can be unit-tested against known values."""

import numpy as np
import pandas as pd
from scipy import stats as st

CONSTRUCTS = ["PU", "PEOU", "TR", "CO", "AC", "WA"]
PREDICTORS = ["PU", "PEOU", "TR", "CO", "AC"]
LABELS = {"PU": "Usefulness", "PEOU": "Ease of use", "TR": "Trust", "CO": "Cost", "AC": "Accessibility", "WA": "Willingness to adopt"}
MIN_N_REGRESSION = 30


def recode(value: int, reverse: bool) -> int:
    return 6 - value if reverse else value


def item_frame(rows: list[tuple[int, str, str, int, bool]]) -> pd.DataFrame:
    """rows = (response_id, construct, item_code, value, is_reverse) -> wide frame of recoded items."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["rid", "construct", "code", "value", "rev"])
    df["value"] = np.where(df["rev"], 6 - df["value"], df["value"])
    return df.pivot(index="rid", columns="code", values="value")


def construct_scores(items: pd.DataFrame, item_construct: dict[str, str]) -> pd.DataFrame:
    out = {}
    for c in CONSTRUCTS:
        cols = [k for k, v in item_construct.items() if v == c and k in items.columns]
        if cols:
            out[c] = items[cols].mean(axis=1)
    return pd.DataFrame(out)


def cronbach_alpha(items: pd.DataFrame) -> float | None:
    k = items.shape[1]
    if k < 2 or len(items) < 2:
        return None
    var_sum = items.var(axis=0, ddof=1).sum()
    total_var = items.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return None
    return float(k / (k - 1) * (1 - var_sum / total_var))


def reliability(items: pd.DataFrame, item_construct: dict[str, str]) -> list[dict]:
    res = []
    for c in CONSTRUCTS:
        cols = [k for k, v in item_construct.items() if v == c and k in items.columns]
        a = cronbach_alpha(items[cols]) if cols else None
        res.append(
            {
                "construct": c,
                "label": LABELS[c],
                "items": len(cols),
                "alpha": None if a is None else round(a, 3),
                "acceptable": bool(a is not None and a >= 0.7),
            }
        )
    return res


def descriptives(scores: pd.DataFrame) -> list[dict]:
    out = []
    for c in scores.columns:
        s = scores[c].dropna()
        out.append(
            {
                "construct": c,
                "label": LABELS[c],
                "n": int(s.size),
                "mean": round(float(s.mean()), 2),
                "sd": round(float(s.std(ddof=1)), 2) if s.size > 1 else None,
                "median": round(float(s.median()), 2),
                "min": round(float(s.min()), 2),
                "max": round(float(s.max()), 2),
            }
        )
    return out


def correlations(scores: pd.DataFrame) -> dict:
    cols = list(scores.columns)
    pearson, spearman, p_values = [], [], []
    for a in cols:
        pr, sr, pp = [], [], []
        for b in cols:
            if a == b:
                pr.append(1.0)
                sr.append(1.0)
                pp.append(0.0)
                continue
            x, y = scores[a], scores[b]
            r, p = st.pearsonr(x, y)
            rho, _ = st.spearmanr(x, y)
            pr.append(round(float(r), 3))
            sr.append(round(float(rho), 3))
            pp.append(round(float(p), 4))
        pearson.append(pr)
        spearman.append(sr)
        p_values.append(pp)
    return {"constructs": cols, "pearson": pearson, "spearman": spearman, "p_values": p_values}


def regression(scores: pd.DataFrame) -> dict:
    """OLS: WA ~ PU + PEOU + TR + CO + AC, with standardised betas and VIF."""
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    cols = [c for c in PREDICTORS if c in scores.columns]
    df = scores[cols + ["WA"]].dropna()
    if len(df) < MIN_N_REGRESSION:
        return {"ready": False, "n": int(len(df)), "min_n": MIN_N_REGRESSION}
    X = sm.add_constant(df[cols])
    m = sm.OLS(df["WA"], X).fit()
    z = (df - df.mean()) / df.std(ddof=1)
    beta = sm.OLS(z["WA"], z[cols]).fit().params
    ci = m.conf_int()
    coefs = []
    for c in cols:
        vif = float(variance_inflation_factor(X.values, list(X.columns).index(c)))
        coefs.append(
            {
                "construct": c,
                "label": LABELS[c],
                "b": round(float(m.params[c]), 3),
                "beta": round(float(beta[c]), 3),
                "se": round(float(m.bse[c]), 3),
                "t": round(float(m.tvalues[c]), 2),
                "p": round(float(m.pvalues[c]), 4),
                "ci_low": round(float(ci.loc[c, 0]), 3),
                "ci_high": round(float(ci.loc[c, 1]), 3),
                "vif": round(vif, 2),
                "significant": bool(m.pvalues[c] < 0.05),
            }
        )
    sig = sorted([c for c in coefs if c["significant"]], key=lambda c: -abs(c["beta"]))
    summary = f"The model explains {m.rsquared * 100:.0f}% of the variation in willingness to adopt. " + (
        f"Strongest significant predictor: {sig[0]['label']} (β = {sig[0]['beta']})."
        if sig
        else "No predictor is statistically significant at the 5% level."
    )
    return {
        "ready": True,
        "n": int(len(df)),
        "r2": round(float(m.rsquared), 3),
        "adj_r2": round(float(m.rsquared_adj), 3),
        "f": round(float(m.fvalue), 2),
        "f_p": round(float(m.f_pvalue), 4),
        "intercept": round(float(m.params["const"]), 3),
        "coefficients": coefs,
        "summary": summary,
    }


def group_difference(scores: pd.DataFrame, groups: pd.Series) -> dict | None:
    """Kruskal-Wallis on WA across groups; groups smaller than 5 are suppressed (anonymity)."""
    df = pd.DataFrame({"WA": scores["WA"], "g": groups}).dropna()
    sizes = df.groupby("g").size()
    keep = sizes[sizes >= 5].index
    df = df[df["g"].isin(keep)]
    if df["g"].nunique() < 2:
        return None
    samples = [g["WA"].values for _, g in df.groupby("g")]
    h, p = st.kruskal(*samples)
    return {
        "h": round(float(h), 3),
        "p": round(float(p), 4),
        "groups": {str(k): {"n": int(len(v)), "mean_wa": round(float(v["WA"].mean()), 2)} for k, v in df.groupby("g")},
    }
