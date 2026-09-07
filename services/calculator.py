from pathlib import Path

import pandas as pd

from core.exceptions import (
    InvalidCityException,
    InvalidGoalException,
    InvalidReferenceDataException,
    UnrealisticGoalException,
)


class FinancialEngine:
    INFLATION_RATE = 0.06
    ANNUAL_RETURN = 0.12
    GOALS = ("Marriage", "Car", "Home")
    REQUIRED_COLUMNS = {
        "City", "Area_Type", "Marriage_Cost_Current", "Car_Cost_Current", "Home_Cost_Current"
    }

    def __init__(self, costs_file: str | Path = "city_goal_costs.csv"):
        try:
            self.city_data = pd.read_csv(costs_file)
        except (OSError, pd.errors.ParserError) as error:
            raise InvalidReferenceDataException(
                f"Could not read the city reference dataset: {error}"
            ) from error

        missing_columns = self.REQUIRED_COLUMNS.difference(self.city_data.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise InvalidReferenceDataException(f"City reference data is missing: {missing}.")

        for column in ("Marriage_Cost_Current", "Car_Cost_Current", "Home_Cost_Current"):
            if pd.to_numeric(self.city_data[column], errors="coerce").isna().any():
                raise InvalidReferenceDataException(f"City reference data has invalid values in {column}.")

    def get_current_cost(self, city: str, goal: str) -> float:
        if goal not in self.GOALS:
            raise InvalidGoalException(goal)

        normalized_city = city.strip().casefold()
        city_rows = self.city_data[
            self.city_data["City"].astype(str).str.strip().str.casefold() == normalized_city
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
        salary: float, saving_percentage: float, required_monthly: float, monthly_emi: float = 0
    ) -> dict[str, float | str]:
        monthly_capacity = salary * (saving_percentage / 100)
        shortfall = required_monthly - monthly_capacity

        if shortfall <= 0:
            feasibility_status = "Achievable"
        elif shortfall <= 0.20 * monthly_capacity:
            feasibility_status = "Challenging"
        else:
            feasibility_status = "Highly Challenging"

        if feasibility_status == "Achievable":
            recommendation = "Your planned saving capacity covers the combined monthly target. Keep an emergency buffer alongside these goals."
        elif feasibility_status == "Challenging":
            recommendation = "You are close to the target. Consider increasing savings slightly or extending the shortest timeline."
        else:
            recommendation = "The target is currently above your saving capacity. Extend timelines, increase savings gradually, or prioritize one goal first."

        return {
            "monthly_capacity": round(monthly_capacity, 2),
            "monthly_emi": round(monthly_emi, 2),
            "monthly_capacity_after_emi": round(max(0, monthly_capacity - monthly_emi), 2),
            "total_required": round(required_monthly, 2),
            "shortfall": round(max(0, shortfall), 2),
            "surplus": round(abs(min(0, shortfall)), 2),
            "status": feasibility_status,
            "recommendation": recommendation,
        }
