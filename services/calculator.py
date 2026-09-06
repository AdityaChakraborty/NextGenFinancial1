from pathlib import Path

import pandas as pd

from core.exceptions import InvalidCityException, InvalidGoalException, UnrealisticGoalException


class FinancialEngine:
    INFLATION_RATE = 0.06
    ANNUAL_RETURN = 0.12
    GOALS = ("Marriage", "Car", "Home")

    def __init__(self, costs_file: str | Path = "city_goal_costs.csv"):
        self.city_data = pd.read_csv(costs_file)

    def get_current_cost(self, city: str, goal: str) -> float:
        if goal not in self.GOALS:
            raise InvalidGoalException(goal)

        city_rows = self.city_data[
            self.city_data["City"].astype(str).str.casefold() == city.casefold()
        ]
        if city_rows.empty:
            raise InvalidCityException(city)

        central_rows = city_rows[city_rows["Area_Type"].astype(str).str.casefold() == "central"]
        if central_rows.empty:
            raise InvalidCityException(f"{city} (Central area unavailable)")

        return float(central_rows.iloc[0][f"{goal}_Cost_Current"])

    @classmethod
    def calculate_future_cost(cls, current_cost: float, years: int) -> float:
        if years <= 0:
            raise UnrealisticGoalException()
        return current_cost * (1 + cls.INFLATION_RATE) ** years

    @classmethod
    def required_monthly_investment(cls, future_cost: float, years: int) -> float:
        if years <= 0:
            raise UnrealisticGoalException()
        monthly_rate = cls.ANNUAL_RETURN / 12
        months = years * 12
        return (future_cost * monthly_rate) / ((1 + monthly_rate) ** months - 1)

    @staticmethod
    def feasibility_analysis(
        salary: float, saving_percentage: float, required_monthly: float
    ) -> dict[str, float | str]:
        monthly_capacity = salary * (saving_percentage / 100)
        shortfall = required_monthly - monthly_capacity

        if shortfall <= 0:
            feasibility_status = "Achievable"
        elif shortfall <= 0.20 * monthly_capacity:
            feasibility_status = "Challenging"
        else:
            feasibility_status = "Highly Challenging"

        return {
            "monthly_capacity": round(monthly_capacity, 2),
            "total_required": round(required_monthly, 2),
            "shortfall": round(max(0, shortfall), 2),
            "surplus": round(abs(min(0, shortfall)), 2),
            "status": feasibility_status,
        }
