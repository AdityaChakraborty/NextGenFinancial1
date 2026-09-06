from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class PreparedSalaryData:
    frame: pd.DataFrame
    features: list[str]
    target: str
    dropped_columns: list[str]
    row_count_before: int
    row_count_after: int


def load_and_clean_salary_data(csv_path: str | Path) -> PreparedSalaryData:
    """Clean the salary dataset and remove fields excluded from prediction."""
    data = pd.read_csv(csv_path)
    row_count_before = len(data)

    data = data.dropna(axis=1, how="all").drop_duplicates()
    data.columns = [str(column).strip() for column in data.columns]
    target = "Monthly_Salary"
    if target not in data.columns:
        raise ValueError(f"Required target column '{target}' is missing.")

    data[target] = pd.to_numeric(data[target], errors="coerce")
    data = data.dropna(subset=[target])
    data = data[data[target] > 0]

    protected_or_unhelpful = [
        column for column in ("Age", "Gender", "Name", "Unnamed: 5") if column in data.columns
    ]
    data = data.drop(columns=protected_or_unhelpful)
    feature_columns = [column for column in data.columns if column != target]

    if not feature_columns:
        raise ValueError("No usable feature columns remain after cleaning.")

    for column in feature_columns:
        if not pd.api.types.is_numeric_dtype(data[column]):
            data[column] = data[column].fillna("Unknown").astype(str).str.strip()
        else:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=feature_columns)

    return PreparedSalaryData(
        frame=data.reset_index(drop=True),
        features=feature_columns,
        target=target,
        dropped_columns=protected_or_unhelpful,
        row_count_before=row_count_before,
        row_count_after=len(data),
    )
