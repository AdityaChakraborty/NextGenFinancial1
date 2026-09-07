# Next Gen Financial Report

## Objective

This local application helps students and early-career users estimate the future cost of their goals. The user supplies their name, age, experience level (`0-1` Fresher, `1-3` Experienced, or `3-5` Expert), city, education, job role, real salary, saving percentage, and timeline for each goal.

## Data

`city_goal_costs.csv` is the reference dataset. The engine selects the Central area row for the chosen city and reads the current Marriage, Car, and Home costs. The local salary model uses city, education, and job role to predict a comparison salary; the entered real salary controls the goal calculation.

## Formulas and assumptions

Future cost:

`future_cost = current_cost * (1 + inflation_rate) ** years`

Required monthly investment:

`monthly_rate = annual_return / 12`

`months = years * 12`

`monthly_investment = future_cost * monthly_rate / ((1 + monthly_rate) ** months - 1)`

The UI defaults to the project assumptions of 6% inflation and 12% annual return. Both can be adjusted for scenario testing; they are educational assumptions, not guarantees.

## Feasibility rules

- Available monthly capacity = entered real salary x saving percentage / 100.
- **Achievable:** required investment is less than or equal to capacity.
- **Challenging:** shortfall is greater than zero but no more than 20% of capacity.
- **Highly Challenging:** shortfall is greater than 20% of capacity.

The interface always shows the required amount, available capacity, and shortfall or surplus.

The planner also gives a rule-based next-step recommendation and supports downloading the deterministic result as a JSON file for local record keeping.

Users may add up to eight custom goals. Each custom goal has a name, current estimated cost, timeline slider, and monthly/yearly contribution frequency. Built-in options are Marriage, Home, Education, Vacation / Trip, Car / Bike, and Emergency Fund. Emergency Fund starts with a one-year timeline and is Paused until selected. Each goal can be switched between Planned and Paused and customised before calculation. Every enabled goal follows the same inflation and return assumptions. Blank, duplicate, invalid, or excessive goals are rejected with a readable validation error.

## Scope

The app is fully local. It does not use Supabase, paid APIs, RAG, or an external LLM. The included salary model is a local educational experiment, not professional financial advice.

This is an educational financial-planning simulation, not professional financial advice.

## Investment option scenarios

The suggestion section models five educational routes for the selected priority goal: mutual funds at 12%, fixed deposits at 6.5%, gold at 7%, stocks at 14%, and real estate at 9% annual return assumptions. For every option it calculates the monthly amount and yearly amount needed to reach that goal's projected future cost within its timeline. The displayed yearly amount is calculated from the unrounded monthly model, so it may differ slightly from the visible monthly amount multiplied by 12 because both values are rounded for display. Projected growth is scenario math, not a promise of return.

## Profile salary model

The project includes a local salary-prediction model. It uses city, education, and job role as primary profile features for a comparison estimate. The entered real salary remains the affordability input, and the model remains an educational estimate rather than a reliable compensation benchmark.

### Data preparation

The pipeline removes the empty trailing CSV column, duplicate rows, invalid target rows, and unused columns. `Age` is removed from model features to reduce demographic profiling. The remaining `City`, `Education`, and `Job_Role` values are treated as categorical features and one-hot encoded. Numeric features, if added later, are standardized. Unknown categories are handled without crashing inference.

### Model selection

The training command compares Gradient Boosting, Random Forest, Extra Trees, and an `MLPRegressor` neural-network baseline using five-fold cross-validated mean absolute error. Gradient Boosting was tuned with shallow trees, a low learning rate, and Huber loss. On the supplied 100-row dataset, the measured result was:

| Model | Cross-validated MAE | Test MAE | Test R2 |
| --- | ---: | ---: | ---: |
| Gradient Boosting | 21,696.88 | 27,873.41 | -0.53 |
| Random Forest | 22,018.21 | 31,052.08 | -0.84 |
| Extra Trees | 24,175.88 | 35,267.87 | -1.20 |
| MLP neural network | 57,924.45 | 60,849.62 | -5.15 |

Gradient Boosting is selected because it has the lowest cross-validated MAE. XGBoost was not added because it is not installed and the small 100-row dataset does not justify introducing another dependency without a measured improvement. The negative test R2 and small dataset mean this is a demonstration model, not a reliable salary benchmark. More representative data and stronger validation would be required before real use.
