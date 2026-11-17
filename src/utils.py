from collections.abc import Mapping

import pandas as pd


def map_codes(series: pd.Series, labels: Mapping[object, str]) -> pd.Series:
    mapped = series.map(labels)
    return mapped.where(mapped.notna(), series.astype("string"))
