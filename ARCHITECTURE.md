# Architecture and DFD

```mermaid
flowchart LR
    User[Student in desktop browser] --> UI[HTML CSS JavaScript UI]
    UI -->|POST /api/v1/plan| API[FastAPI local API]
    API --> Engine[FinancialEngine]
    Engine --> CSV[(city_goal_costs.csv)]
    Engine --> Formula[Inflation and investment formulas]
    Formula --> Feasibility[Capacity and feasibility rules]
    Feasibility --> API
    API -->|JSON results| UI
    UI --> Results[Goal cards and monthly analysis]
```

## Request flow

1. The student fills the local browser form.
2. JavaScript sends the values to the local FastAPI endpoint.
3. `FinancialEngine` loads the selected city's Central-area costs from `city_goal_costs.csv`.
4. The engine calculates future costs, monthly investments, and total feasibility.
5. FastAPI returns deterministic JSON.
6. The browser displays current cost, future cost, monthly investment, capacity, and shortfall/surplus.
