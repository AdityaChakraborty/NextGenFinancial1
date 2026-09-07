# Next Gen Financial: Project Guide

## 1. What the project does

Next Gen Financial is a local educational financial-planning application for students and early-career users. A user enters their name, age, city, education, job role, salary fallback, saving percentage, assumptions, and selected goals. The application uses the profile fields to estimate salary, reads city costs from `city_goal_costs.csv`, projects each goal into the future, calculates the required investment, and checks whether saving capacity is enough.

The application is intentionally local. It does not require Supabase, a paid API, RAG, or an external LLM. Its local salary prediction model is used when the trained artifact is available.

The salary model uses `salary_data.csv`; `Age` is removed from model features to reduce demographic profiling, categorical fields are one-hot encoded, numeric fields are scaled, and three candidates are compared with cross-validation. The selected artifact supports both the salary endpoint and the main planner's profile-based affordability calculation.

## 2. Project structure

```text
main.py                         FastAPI routes, request models, and orchestration
services/calculator.py          CSV loading, city lookup, formulas, feasibility rules
services/recommendations.py     Priority planning and investment education cards
core/exceptions.py              Domain and reference-data HTTP errors
static/index.html               Browser structure and form controls
static/style.css                Visual design and responsive layout
static/app.js                   Browser state, sliders, goal cards, API calls, results
city_goal_costs.csv             City and Central-area reference costs
salary_data.csv                 Optional training data for salary modeling
data_pipeline/preprocess.py     Cleaning, bias reduction, and feature preparation
ml_models/salary_predictor.py   Model comparison, training, evaluation, and inference
train_model.py                  Reproducible training command
README.md                       Setup and short project rules
DEMO_GUIDE.md                   Presentation script and explanation notes
PROJECT_REPORT.md               Capstone formulas and assumptions
ARCHITECTURE.md                 DFD and request-flow diagram
```

## 3. Request flow

1. The browser loads the city list and default goal costs from FastAPI.
2. The user chooses a city, edits goal costs and timelines, pauses or plans goals, and selects monthly or yearly contribution display.
3. JavaScript collects only enabled goals and sends JSON to `POST /api/v1/plan`.
4. Pydantic validates every request field before the calculation runs.
5. `calculate_selected_goal()` projects each enabled goal and calculates its monthly investment.
6. The local salary model estimates monthly salary from city, education, and job role when available; entered salary is the fallback.
7. `FinancialEngine.feasibility_analysis()` compares the combined monthly requirement to the profile-based saving capacity.
7. FastAPI returns deterministic JSON; JavaScript renders the cards, recommendation, and analysis.

## 4. Backend functions and classes

### `core/exceptions.py`

Contains named HTTP exceptions for invalid cities, unsupported goals, impossible timelines, malformed reference data, and general planner failures. Naming these cases keeps domain failures readable at the API boundary.

### `GoalRequest` in `main.py`

Defines one enabled goal in an API request. It contains the goal name, current cost, years, and contribution frequency. It limits names to 60 characters, costs to INR 1,000,000,000, timelines to 1–60 years, and frequency to `monthly` or `yearly`.

### `GoalRequest.strip_name()`

Removes leading and trailing whitespace before validating a goal name. A blank name therefore fails the minimum-length rule.

### `GoalRequest.reject_non_finite_cost()`

Rejects `NaN` and infinite costs so invalid numeric values cannot enter the formulas.

### `PlanRequest`

Defines the complete planner request: name, age, city, education, job role, salary fallback, saving percentage, inflation rate, annual return, and one to twelve goals. Salary is limited to INR 1,000–10,000,000 per month.

### `PlanRequest.strip_text()`

Trims the user's name and city before the request is processed.

### `PlanRequest.reject_non_finite_numbers()`

Rejects non-finite salary, saving percentage, inflation, and return values.

### `PlanRequest.reject_duplicate_goals()`

Prevents two enabled goals from having the same name, ignoring capitalization.

### `validation_exception_handler()`

Converts FastAPI/Pydantic validation errors into a consistent JSON response with a readable `detail` and a list of `{field, message}` objects for the frontend.

### `calculate_goal()`

Legacy helper for looking up a standard CSV goal and calculating it with the original fixed engine assumptions. The current selectable-goal route uses `calculate_selected_goal()` instead.

### `calculate_selected_goal()`

Calculates one selected goal using the user's current cost, timeline, inflation slider, and annual-return slider. It returns current cost, future cost, monthly investment, yearly investment, selected frequency, and the displayed contribution amount.

### `frontend()`

Serves `static/index.html` at `/`.

### `health()`

Returns `{ "status": "ok" }` at `/health` so the local server can be checked quickly.

### `list_cities()`

Returns the unique city names read from the CSV at `/api/v1/cities`.

### `default_goals()`

Returns the five built-in choices for a selected city: Marriage, Home, Education, Vacation / Trip, and Car / Bike. Marriage, Home, and Car / Bike use the city's Central-area CSV costs. Education and Vacation / Trip use local project defaults.

### `generate_plan()`

The main `/api/v1/plan` endpoint. It calculates all enabled goals, sums their monthly requirements, runs the feasibility analysis, and returns the complete plan and assumptions.

### ML routes

`ml_status()` reports whether the local joblib artifact exists and returns the selected model, feature list, data-cleaning report, and evaluation records. `predict_salary_endpoint()` accepts city, education, and job role and delegates to the persisted pipeline. The main planner also calls this pipeline when the artifact exists.

### `ml_status()` and `predict_salary_endpoint()`

These endpoints report the trained model and predict monthly salary from city, education, and job role. `/api/v1/plan` uses the same profile prediction for affordability and returns the salary source in `calculation_profile`.

## 4.1 Recommendation functions

### `build_suggestion_plan()` in `services/recommendations.py`

Sorts enabled goals by timeline, selects the nearest goal as the first priority, and adapts the advice to the result status. An Achievable plan receives a protection-and-growth message; a Challenging plan receives gap-closing advice; and a Highly Challenging plan receives prioritization and timeline-extension advice.

It also returns three practical next steps and educational overview cards for mutual funds, gold, stocks, and real estate. These are not personalized financial advice or product recommendations; each card explains a broad use, risk level, and planning consideration.

The cards also include Fixed Deposit (FD). One portfolio-level monthly contribution is divided equally across all five categories. Each option uses an illustrative annual rate, projects its equal share through the selected tenure, and the UI adds all projected values together. These figures are scenarios, not guaranteed returns.

The browser lets the user adjust one portfolio contribution slider. `updateInvestmentPortfolio()` divides it equally across the option cards, recalculates each compound projected value and gap/surplus, while `updateInvestmentTotals()` aggregates the equal contributions and projected values. The note explains that the categories are combined for the selected portfolio scenario, not a recommendation to buy every product.

## 5. Calculation engine functions

### `FinancialEngine.__init__()`

Loads `city_goal_costs.csv` with Pandas and verifies that the required columns exist and contain numeric costs. Invalid or missing reference data raises a clear server error.

### `FinancialEngine.get_current_cost()`

Matches the requested city case-insensitively, selects its `Central` row, and returns the current cost for Marriage, Car, or Home. Unknown cities and unsupported goals raise clear exceptions.

### `FinancialEngine.calculate_future_cost()`

Legacy class method using the default 6% inflation assumption. The selectable plan route applies the user's slider directly in `calculate_selected_goal()`.

### `FinancialEngine.required_monthly_investment()`

Legacy class method using the default 12% return assumption. The selectable plan route applies the user's return slider directly.

### `FinancialEngine.feasibility_analysis()`

Calculates monthly capacity, total required investment, shortfall/surplus, classification, and a recommendation.

Rules:

- Achievable: required amount is within capacity.
- Challenging: shortfall is no more than 20% of capacity.
- Highly Challenging: shortfall is greater than 20% of capacity.

## 5.1 Data files and generated files

`city_goal_costs.csv` supplies the city-level Marriage, Car, and Home cost values used by the core planner. `salary_data.csv` is a separate, optional training dataset. The `artifacts/` folder is created during training and contains a local joblib model; generated artifacts are ignored by Git and can be recreated with `python train_model.py`.

`requirements.txt` lists the runtime, data-processing, and model-training dependencies. `tests/test_project.py` verifies the main routes, salary boundaries, duplicate/empty goals, reference lookup, and recommendation output. Package `__init__.py` files mark `core`, `services`, `data_pipeline`, and `ml_models` as importable Python packages.

## 6. Frontend JavaScript functions

### `goalCard()`

Builds the HTML for one built-in or custom goal card, including its Planned/Paused state, cost, timeline slider, number field, and monthly/yearly selector.

### `connectGoalCard()`

Attaches interactive behavior to a goal card. It keeps the range slider and year number synchronized, updates Planned/Paused text, and removes custom cards when requested.

### `loadGoalOptions()`

Fetches city-specific defaults from `/api/v1/default-goals` and renders the five built-in goal cards.

### `addCustomGoal()`

Adds a new custom goal card, gives it an editable name, and limits custom goals to eight.

### `collectGoals()`

Reads only cards marked Planned, converts cost and timeline values to numbers, and returns the request-ready goal list.

### `renderGoalCards()`

Displays current cost, projected cost, and the chosen monthly/yearly contribution for each result.

### `renderAnalysis()`

Displays the feasibility status, monthly requirement, capacity, difference, and recommendation.

### `showError()`

Converts structured API validation errors into a readable message for the form alert.

### Form submit handler

Prevents a page reload, validates that at least one goal is Planned, converts numeric inputs, posts the plan to FastAPI, and renders the returned results.

### `syncAssumption()`

Updates the visible percentage beside an inflation or annual-return slider.

### Download handler

Serializes the latest returned plan into `financial-dream-plan.json` for local download.

## 6.1 Visual file responsibilities

`static/index.html` defines the form, dynamic goal mount point, result areas, recommendation panel, investment cards, and model insight panel. `static/style.css` defines the green editorial palette, range controls, responsive grids, result panels, and mobile breakpoints. `static/app.js` supplies the behavior that HTML and CSS cannot provide: fetching city data, creating cards, collecting only Planned goals, calling the API, updating projections, and downloading a JSON snapshot.

## 7. User-input edge cases

- Salary below INR 1,000: rejected.
- Salary above INR 10,000,000: rejected.
- Text, `NaN`, infinity, zero, or negative numeric values: rejected.
- Age outside 18–100: rejected.
- Saving percentage outside 0–100: rejected.
- Inflation outside 0–20%: rejected.
- Annual return outside 0–30%: rejected.
- Goal cost outside INR 1,000–1,000,000,000: rejected.
- Goal timeline outside 1–60 years: rejected.
- Unsupported contribution frequency: rejected.
- Duplicate goal names: rejected.
- No Planned goals: rejected in the browser before calculation.
- Missing or malformed CSV columns: rejected during startup.
- Unknown city: returns a clear not-found error.

## 8. Run locally

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000` in a desktop browser. API documentation is available at `http://127.0.0.1:8000/docs`.

The project uses Python 3.13 for the local environment. The pinned versions in
`requirements.txt` include FastAPI 0.115.6, Uvicorn 0.34.0, Pandas 2.2.3,
Pydantic 2.10.5, scikit-learn 1.6.1, joblib 1.4.2, and httpx 0.28.1.
`httpx` is included because the FastAPI test client depends on it.
