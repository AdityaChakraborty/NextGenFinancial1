import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from services.calculator import FinancialEngine
from services.recommendations import build_suggestion_plan


ROOT = Path(__file__).resolve().parents[1]


class PlannerApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.base = {
            "name": "Rahul",
            "age": 22,
            "city": "Bangalore",
            "salary": 40000,
            "saving_percentage": 20,
            "inflation_rate": 6,
            "annual_return": 12,
            "goals": [
                {"name": "Marriage", "current_cost": 890000, "years": 5, "frequency": "monthly"}
            ],
        }

    def test_health_and_city_routes(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        cities = self.client.get("/api/v1/cities").json()
        self.assertIn("Bangalore", cities)

    def test_plan_contains_goal_analysis_and_suggestions(self):
        response = self.client.post("/api/v1/plan", json=self.base)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["goals"][0]["name"], "Marriage")
        self.assertIn("analysis", body)
        self.assertEqual(len(body["suggestion_plan"]["investment_options"]), 5)

    def test_salary_boundaries_and_invalid_goal_cost(self):
        for salary, expected_status in ((999, 422), (1000, 200), (10_000_000, 200), (10_000_001, 422)):
            response = self.client.post("/api/v1/plan", json={**self.base, "salary": salary})
            self.assertEqual(response.status_code, expected_status)
        invalid_goal = {**self.base, "goals": [{**self.base["goals"][0], "current_cost": 999}]}
        self.assertEqual(self.client.post("/api/v1/plan", json=invalid_goal).status_code, 422)

    def test_empty_and_duplicate_goals_are_rejected(self):
        self.assertEqual(self.client.post("/api/v1/plan", json={**self.base, "goals": []}).status_code, 422)
        duplicate = {**self.base, "goals": [self.base["goals"][0], {**self.base["goals"][0], "name": " marriage "}]}
        self.assertEqual(self.client.post("/api/v1/plan", json=duplicate).status_code, 422)


class DomainTests(unittest.TestCase):
    def test_reference_data_and_recommendation(self):
        engine = FinancialEngine(ROOT / "city_goal_costs.csv")
        self.assertEqual(engine.get_current_cost("Bangalore", "Home"), 9400000.0)
        plan = build_suggestion_plan(
            [{"name": "Emergency Fund", "years": 1, "monthly_sip": 25000, "future_cost": 300000}],
            {"status": "Highly Challenging"},
            22,
        )
        self.assertEqual(plan["priority_goal"], "Emergency Fund")
        self.assertEqual(len(plan["investment_options"]), 5)


if __name__ == "__main__":
    unittest.main()