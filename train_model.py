import argparse
import json

from ml_models.salary_predictor import train_salary_predictor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and compare salary prediction models.")
    parser.add_argument("--data", default="salary_data.csv")
    parser.add_argument("--artifact", default="artifacts/salary_predictor.joblib")
    args = parser.parse_args()
    result = train_salary_predictor(args.data, args.artifact)
    print(json.dumps({
        "selected_model": result["selected_model"],
        "reports": result["reports"],
        "data_report": result["data_report"],
    }, indent=2))
