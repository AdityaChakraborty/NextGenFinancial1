# Next Gen Financial Report

## Objective

This local application helps fresher students estimate the future cost of their goals. The user supplies their name, age, city, education, job role, salary fallback, saving percentage, and timeline for each goal.

## Data

`city_goal_costs.csv` is the reference dataset. The engine selects the Central area row for the chosen city and reads the current Marriage, Car, and Home costs. The local salary model uses city, education, and job role to estimate monthly salary; the entered salary is used only if the model artifact is unavailable.

## Formulas and assumptions

Future cost:

`future_cost = current_cost * (1 + inflation_rate) ** years`

Required monthly investment:

`monthly_rate = annual_return / 12`

`months = years * 12`

`monthly_investment = future_cost * monthly_rate / ((1 + monthly_rate) ** months - 1)`

The UI defaults to the project assumptions of 6% inflation and 12% annual return. Both can be adjusted for scenario testing; they are educational assumptions, not guarantees.

## Feasibility rules

- Available monthly capacity = profile salary estimate x saving percentage / 100.
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

The project includes a local salary-prediction model. It uses city, education, and job role as primary profile features for the planner's affordability calculation. The entered salary is a fallback, and the model remains an educational estimate rather than a reliable compensation benchmark.

### Data preparation

The pipeline removes the empty trailing CSV column, duplicate rows, invalid target rows, and unused columns. `Age` is removed from model features to reduce demographic profiling. The remaining `City`, `Education`, and `Job_Role` values are treated as categorical features and one-hot encoded. Numeric features, if added later, are standardized. Unknown categories are handled without crashing inference.

### Model selection

The training command compares Extra Trees, Random Forest, and an `MLPRegressor` neural-network baseline using five-fold cross-validated mean absolute error. On the supplied 100-row dataset, the measured result was:

| Model | Cross-validated MAE | Test MAE | Test R2 |
| --- | ---: | ---: | ---: |
| Extra Trees | 24,175.88 | 35,267.87 | -1.20 |
| Random Forest | 21,976.66 | 29,700.64 | -0.66 |
| MLP neural network | 57,924.45 | 60,849.62 | -5.15 |

Random Forest was selected because it had the lowest cross-validated MAE. The negative test R2 and small dataset mean this is a demonstration model, not a reliable salary benchmark. More representative data and stronger validation would be required before real use.
