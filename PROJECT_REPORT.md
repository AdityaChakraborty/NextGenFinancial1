# Financial Dream Planner Report

## Objective

This local application helps fresher students estimate the future cost of three goals: Marriage, Car, and Home. The user supplies their name, age, city, salary, saving percentage, and timeline for each goal.

## Data

`city_goal_costs.csv` is the reference dataset. The engine selects the Central area row for the chosen city and reads the current Marriage, Car, and Home costs. Salary is entered directly by the user; no salary prediction or ML training is used.

## Formulas and assumptions

Future cost:

`future_cost = current_cost * (1 + 0.06) ** years`

Required monthly investment:

`monthly_rate = 0.12 / 12`

`months = years * 12`

`monthly_investment = future_cost * monthly_rate / ((1 + monthly_rate) ** months - 1)`

The 6% inflation rate and 12% annual return are educational project assumptions, not guarantees.

## Feasibility rules

- Available monthly capacity = salary x saving percentage / 100.
- **Achievable:** required investment is less than or equal to capacity.
- **Challenging:** shortfall is greater than zero but no more than 20% of capacity.
- **Highly Challenging:** shortfall is greater than 20% of capacity.

The interface always shows the required amount, available capacity, and shortfall or surplus.

The planner also gives a rule-based next-step recommendation and supports downloading the deterministic result as a JSON file for local record keeping.

## Scope

The app is fully local. It does not use Supabase, paid APIs, RAG, an external LLM, or a salary model. The optional Agentic AI component is intentionally not included in this basic implementation.

This is an educational financial-planning simulation, not professional financial advice.
