"""Verify the analytics against hand-computed / independently known values."""

import numpy as np
import pandas as pd
import pytest

from app.analytics import stats as S


def test_cronbach_alpha_known_value():
    # Classic worked example: 4 respondents x 3 items
    df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 3, 4, 5], "c": [1, 3, 3, 5]})
    # item variances 5/3, 5/3, 8/3 -> sum 6 ; totals 4,8,10,14 -> variance 52/3
    expected = 3 / 2 * (1 - 6 / (52 / 3))  # = 0.98077
    assert S.cronbach_alpha(df) == pytest.approx(expected, abs=1e-3)


def test_alpha_undefined_cases():
    assert S.cronbach_alpha(pd.DataFrame({"a": [1, 2, 3]})) is None
    assert S.cronbach_alpha(pd.DataFrame({"a": [3, 3, 3], "b": [3, 3, 3]})) is None


def test_reverse_scoring():
    assert S.recode(1, True) == 5 and S.recode(5, True) == 1 and S.recode(4, False) == 4
    df = S.item_frame([(1, "CO", "CO1", 1, True), (1, "CO", "CO2", 4, False)])
    assert df.loc[1, "CO1"] == 5 and df.loc[1, "CO2"] == 4


def test_descriptives_known():
    sc = pd.DataFrame({"PU": [1.0, 2.0, 3.0, 4.0, 5.0]})
    d = S.descriptives(sc)[0]
    assert d["mean"] == 3.0 and d["median"] == 3.0 and d["sd"] == pytest.approx(1.58, abs=0.01) and d["n"] == 5


def test_correlation_perfect_and_inverse():
    x = pd.Series(np.arange(1, 21, dtype=float))
    c = S.correlations(pd.DataFrame({"PU": x, "TR": x * 2 + 1, "CO": -x}))
    i = {k: n for n, k in enumerate(c["constructs"])}
    assert c["pearson"][i["PU"]][i["TR"]] == 1.0 and c["pearson"][i["PU"]][i["CO"]] == -1.0
    assert c["spearman"][i["PU"]][i["CO"]] == -1.0


def test_regression_recovers_known_coefficients():
    rng = np.random.default_rng(0)
    n = 400
    df = pd.DataFrame({c: rng.normal(3, 1, n) for c in S.PREDICTORS})
    df["WA"] = 1.0 + 0.6 * df["TR"] + 0.3 * df["PU"] - 0.2 * df["CO"] + rng.normal(0, 0.3, n)
    r = S.regression(df)
    b = {c["construct"]: c for c in r["coefficients"]}
    assert r["ready"] and r["r2"] > 0.8
    assert (
        b["TR"]["b"] == pytest.approx(0.6, abs=0.05)
        and b["PU"]["b"] == pytest.approx(0.3, abs=0.05)
        and b["CO"]["b"] == pytest.approx(-0.2, abs=0.05)
    )
    assert b["TR"]["significant"] and not b["AC"]["significant"] and b["TR"]["vif"] < 2
    assert "Trust" in r["summary"]


def test_regression_needs_enough_data():
    df = pd.DataFrame({c: [1.0, 2, 3] for c in S.PREDICTORS + ["WA"]})
    assert S.regression(df) == {"ready": False, "n": 3, "min_n": 30}


def test_group_difference_suppresses_small_groups():
    sc = pd.DataFrame({"WA": [1, 2, 3, 4, 5, 4, 5, 5, 4, 5, 1]})
    groups = pd.Series(["a"] * 5 + ["b"] * 5 + ["tiny"])
    r = S.group_difference(sc, groups)
    assert "tiny" not in r["groups"] and set(r["groups"]) == {"a", "b"}
    assert S.group_difference(sc, pd.Series(["a"] * 11)) is None
