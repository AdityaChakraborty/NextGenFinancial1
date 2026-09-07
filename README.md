# Next Gen Financial

A local FastAPI financial dream planner for fresher students. It uses the supplied city reference data, default 6% inflation, and a documented investment assumption to project marriage, car, and home goals.

## Run locally

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000` for the planner UI or `http://127.0.0.1:8000/docs` for the interactive API documentation.

The project is tested with Python 3.13. The dependency pins in `requirements.txt`
use Python 3.13-compatible FastAPI, Pydantic, Pandas, and scikit-learn releases.
If `python3.13` is not installed, install Python 3.13 first or use another
Python version supported by all pinned packages.

For a complete explanation of the architecture, data flow, formulas, validation, and every backend/frontend function, see [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md). For a presentation script and demonstration sequence, see [`DEMO_GUIDE.md`](DEMO_GUIDE.md).

## Example request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/plan \\
  -H 'Content-Type: application/json' \\
  -d '{
    "name": "Asha",
    "age": 22,
    "city": "Pune",
    "education": "B.Tech",
    "job_role": "Software Engineer",
    "salary": 120000,
    "saving_percentage": 30,
    "goals": [
      {"name": "Marriage", "current_cost": 1000000, "years": 5, "frequency": "monthly"},
      {"name": "Home", "current_cost": 12000000, "years": 10, "frequency": "yearly"}
    ]
  }'
```

## Project rules

- Future cost = current cost x (1 + inflation rate) ^ years; the project default is 6%.
- Required monthly investment uses the selected expected annual return, compounded monthly; the project default is 12%.
- Achievable means the required amount is within the available monthly saving capacity.
- Challenging means the shortfall is at most 20% of capacity; larger shortfalls are Highly Challenging.
- This is an educational simulation, not professional financial advice.

The core planner is fully local and uses `city_goal_costs.csv` as its planning reference. The profile salary model uses `salary_data.csv`. No Supabase, paid API, or RAG is required; model training is optional because entered salary is retained as a fallback.

## Profile salary model

The planner uses the primary profile inputs City, Education, and Job Role with the local salary model to estimate monthly salary. The entered salary remains a fallback if the model artifact is unavailable:

```bash
python train_model.py --data salary_data.csv --artifact artifacts/salary_predictor.joblib
```

The training pipeline cleans the supplied data, removes the empty trailing column and `Age`, compares Extra Trees, Random Forest, and an MLP neural-network baseline, and saves the model with the lowest cross-validated mean absolute error. Check `/api/v1/ml/status` or call `/api/v1/ml/predict-salary` with `City`, `Education`, and `Job_Role` after training. The profile prediction is used for affordability and returned in `calculation_profile`.

The UI also loads the available cities from the API, validates input with readable field-level errors, provides a next-step recommendation, and lets the user download the generated plan as JSON.

After calculation, the separate suggestion section identifies the nearest goal to focus on, gives improvement actions based on Achievable/Challenging/Highly Challenging status, and explains mutual funds, gold, stocks, and real estate as broad educational options with risk and liquidity considerations.

Each investment option uses an equal share of one portfolio contribution slider. Changing the total recalculates each category's projected future value, the summed tenure value, and the selected portfolio total. Name, age, city, education, and job role are primary profile inputs; age shapes the recommendation horizon, city shapes goal costs, and education/job role shape the salary prediction.

Monthly salary must be a numeric value from INR 1,000 to INR 1,00,00,000. Other numeric inputs are also validated for positive values, supported ranges, and finite numbers.

Use **Add custom goal** to add a personal goal such as Education, Travel, Business, or Emergency Fund. Enter its current estimated cost and timeline; it will be included in the same calculation and feasibility analysis. Each built-in and custom goal can be marked Planned or Paused, adjusted with a 1–60 year slider, customised with a cost, and set to monthly or yearly contributions. The inflation and return assumptions also have minimal sliders, starting at the capstone defaults of 6% and 12%.
