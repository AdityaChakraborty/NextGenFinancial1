# Financial Dream Planner

A local FastAPI financial dream planner for fresher students. It uses the supplied city reference data, fixed 6% inflation, and a documented investment assumption to project marriage, car, and home goals.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000` for the planner UI or `http://127.0.0.1:8000/docs` for the interactive API documentation.

## Example request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/plan \\
  -H 'Content-Type: application/json' \\
  -d '{
    "name": "Asha",
    "age": 22,
    "city": "Pune",
    "salary": 120000,
    "saving_percentage": 30,
    "years_to_marriage": 5,
    "years_to_car": 3,
    "years_to_home": 10
  }'
```

## Project rules

- Future cost = current cost x (1 + 0.06) ^ years.
- Required monthly investment uses a 12% expected annual return, compounded monthly.
- Achievable means the required amount is within the available monthly saving capacity.
- Challenging means the shortfall is at most 20% of capacity; larger shortfalls are Highly Challenging.
- This is an educational simulation, not professional financial advice.

The application is fully local and uses `city_goal_costs.csv` as its only reference dataset. No Supabase, paid API, RAG, salary prediction, or ML training is required.
