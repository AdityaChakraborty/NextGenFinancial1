from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from data_pipeline.preprocess import PreparedSalaryData, load_and_clean_salary_data


@dataclass
class ModelReport:
    name: str
    cross_validated_mae: float
    test_mae: float
    test_r2: float


def _make_preprocessor(data: pd.DataFrame, features: list[str]) -> ColumnTransformer:
    numeric_features = data[features].select_dtypes(include="number").columns.tolist()
    categorical_features = [feature for feature in features if feature not in numeric_features]
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ],
        remainder="drop",
    )


def _model_candidates() -> dict[str, Any]:
    return {
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.03,
            max_depth=2,
            loss="huber",
            random_state=42,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            min_samples_leaf=1,
            max_features=1.0,
            n_jobs=-1,
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=250,
            random_state=42,
            min_samples_leaf=2,
            n_jobs=-1,
        ),
        "neural_network": MLPRegressor(hidden_layer_sizes=(64, 32), early_stopping=True, max_iter=1200, random_state=42),
    }


def train_salary_predictor(csv_path: str | Path, artifact_path: str | Path) -> dict[str, Any]:
    """Compare regressors and persist the winner by cross-validated MAE."""
    prepared = load_and_clean_salary_data(csv_path)
    features = prepared.frame[prepared.features]
    target = prepared.frame[prepared.target]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )
    folds = KFold(n_splits=5, shuffle=True, random_state=42)
    reports: list[ModelReport] = []
    fitted: dict[str, Pipeline] = {}

    for name, estimator in _model_candidates().items():
        pipeline = Pipeline([
            ("preprocess", _make_preprocessor(prepared.frame, prepared.features)),
            ("model", estimator),
        ])
        cv_mae = -cross_val_score(
            pipeline, x_train, y_train, cv=folds, scoring="neg_mean_absolute_error", n_jobs=1
        ).mean()
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        reports.append(ModelReport(name, float(cv_mae), float(mean_absolute_error(y_test, predictions)), float(r2_score(y_test, predictions))))
        fitted[name] = pipeline

    winner = min(reports, key=lambda report: report.cross_validated_mae)
    artifact = {
        "pipeline": fitted[winner.name],
        "features": prepared.features,
        "target": prepared.target,
        "selected_model": winner.name,
        "reports": [asdict(report) for report in reports],
        "data_report": {
            "rows_before": prepared.row_count_before,
            "rows_after": prepared.row_count_after,
            "dropped_columns": prepared.dropped_columns,
        },
    }
    artifact_path = Path(artifact_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path)
    return artifact


def predict_salary(artifact_path: str | Path, values: dict[str, Any]) -> dict[str, Any]:
    """Predict a salary from non-demographic profile fields using a trained artifact."""
    artifact = joblib.load(artifact_path)
    features = pd.DataFrame([{feature: values.get(feature, "Unknown") for feature in artifact["features"]}])
    prediction = float(artifact["pipeline"].predict(features)[0])
    return {"predicted_monthly_salary": round(max(0, prediction), 2), "model": artifact["selected_model"]}
