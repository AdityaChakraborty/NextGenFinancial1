# Next Gen Financial: Demonstration Notes

This guide is written for presenting the project in a viva, assessment, or live demonstration. The wording is specific to this implementation and is intended to help explain the decisions without reading source code line by line.

## One-minute explanation

Next Gen Financial is a local web application that turns a user's profile and selected life goals into a transparent savings plan. The user enters name, age, city, education, and job role, edits the cost and timing of each goal, and marks goals as Planned or Paused. The server uses the profile salary estimate, applies the selected inflation and return assumptions, then compares the required monthly amount with saving capacity.

The intelligence layer has two jobs. A rule-based recommendation module decides which goal deserves attention first and explains how to improve the plan. A small, locally trained salary model estimates monthly salary from city, education, and job role; the entered salary is used only as a fallback when the artifact is unavailable.

## Five-minute demonstration

### 1. Start the app

```bash
cd "/Users/adi/Desktop/vscode /webskitters/finalcial calculator"
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000` or the interactive API documentation at
`http://127.0.0.1:8000/docs`. This project uses Python 3.13 and the pinned
dependency versions in `requirements.txt`.

### 2. Show the starting form

Point out:

- Student name and age.
- City loaded from the reference CSV.
- Monthly salary fallback and saving percentage.
- Required education and job role fields used for the profile salary calculation.
- Inflation and annual-return sliders.
- Goal cards with cost, years, contribution frequency, and Planned/Paused state.

### 3. Demonstrate goal editing

Select Bangalore. Keep Marriage, Home, and Car / Bike planned. Pause Home or turn on Emergency Fund to show that only planned goals enter the calculation. Move a timeline slider and switch one goal from Monthly to Yearly.

Click **Add custom goal**, rename it to something such as `Business`, set a cost and timeline, and leave it planned.

### 4. Demonstrate calculation

Use this sample:

- Name: Rahul
- Age: 22
- City: Bangalore
- Education: B.E.
- Job role: Software Engineer
- Salary: ₹40,000
- Saving percentage: 20%
- Inflation: 6%
- Annual return: 12%

Submit the form. Explain that the result contains the current cost, inflation-adjusted future cost, contribution amount, total required amount, available capacity, and the shortfall or surplus.

### 5. Explain the recommendation

The nearest enabled timeline becomes the priority. If the plan is Achievable, the advice focuses on preserving the emergency reserve and continuing contributions. If it is Challenging, the advice focuses on closing a smaller gap. If it is Highly Challenging, the advice recommends prioritising one goal and extending or reshaping other timelines.

### 6. Compare investment scenarios

Scroll to the investment cards. Explain that one monthly portfolio contribution is divided equally across all categories, and their projected values are added at the end of the tenure:

- Mutual funds: diversified long-term growth scenario.
- Fixed deposit: stability-oriented scenario.
- Gold: limited diversification scenario.
- Stocks: higher-risk long-horizon scenario.
- Real estate: large-asset and liquidity planning scenario.

Use the portfolio slider. Show that the equal per-category amount, each projected value, and the summed portfolio projection change immediately.

### 7. Show the profile calculation

Enter `BCA` for education and `Web Developer` for job role, then calculate again. The page shows the locally trained model estimate and uses it for the affordability calculation. The salary field remains available as a fallback.

## How to explain the calculation

For a goal with current cost $C$, inflation rate $i$, and timeline $t$ years:

`future_cost = C x (1 + i) ^ t`

For expected annual return $r$, monthly rate $m = r / 12$, and $n = 12t$ monthly contributions:

`monthly_investment = future_cost x m / ((1 + m) ^ n - 1)`

The available monthly capacity is:

`salary x saving_percentage / 100`

The result classification is:

- Achievable: required amount is no greater than capacity.
- Challenging: the shortfall is positive but no more than 20% of capacity.
- Highly Challenging: the shortfall is greater than 20% of capacity.

## How to explain the data pipeline

The optional salary dataset has 100 rows. The pipeline removes the empty trailing CSV column, duplicate records, invalid salary targets, and `Age` from the model feature set. `City`, `Education`, and `Job_Role` are categorical inputs. They are one-hot encoded inside a scikit-learn pipeline so the same transformation is used during training and prediction.

The training script compares Extra Trees, Random Forest, and an MLP neural-network baseline using shuffled five-fold validation. Random Forest won on cross-validated mean absolute error for this dataset. The negative test R2 is an important limitation: the dataset is small and the model is a demonstration, not a reliable employment or compensation estimator.

## Files to mention

- `main.py`: API application, request validation, routes, and orchestration.
- `services/calculator.py`: city lookup, CSV checks, formulas, and feasibility analysis.
- `services/recommendations.py`: priority logic and investment scenarios.
- `core/exceptions.py`: named HTTP/domain errors.
- `data_pipeline/preprocess.py`: salary-data cleaning and feature selection.
- `ml_models/salary_predictor.py`: preprocessing pipeline, model comparison, persistence, and prediction.
- `train_model.py`: command-line training entrypoint.
- `static/index.html`: page structure and fields.
- `static/app.js`: browser state, API requests, sliders, cards, totals, and download action.
- `static/style.css`: responsive visual system.
- `city_goal_costs.csv`: city goal-cost reference data.
- `salary_data.csv`: optional salary-model training data.
- `tests/test_project.py`: repeatable API and domain checks.
- `PROJECT_GUIDE.md`: detailed function reference.
- `PROJECT_REPORT.md`: formulas, assumptions, and ML evaluation.
- `ARCHITECTURE.md`: data-flow diagram.

## Questions to answer honestly

### Is this professional financial advice?

No. It is an educational simulation using project assumptions. Investment returns are uncertain.

### Why does the model not decide the user's salary?

The assessment says salary is supplied directly. The model is separated as an optional benchmark so it cannot silently alter the main calculation.

### Why is Random Forest used instead of a deep neural network?

The supplied dataset is small and tabular. The measured cross-validation error was lower for Random Forest than for the MLP baseline. Model choice is based on observed validation results, not on the label "deep learning" alone.

### What happens when input is invalid?

Pydantic rejects invalid requests with a structured 422 response. Unknown cities return a clear 404. The browser also blocks missing, out-of-range, and non-numeric fields before submission.
