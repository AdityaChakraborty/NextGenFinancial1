from typing import Any


def _investment_scenario(
    name: str,
    annual_return: float,
    fit: str,
    risk: str,
    note: str,
    future_goal_cost: float,
    years: int,
) -> dict[str, Any]:
    monthly_rate = annual_return / 100 / 12
    months = years * 12
    growth_factor = ((1 + monthly_rate) ** months - 1) / monthly_rate
    return {
        "name": name,
        "fit": fit,
        "risk": risk,
        "note": note,
        "annual_return": annual_return,
        "years": years,
        "goal_amount": round(future_goal_cost, 2),
        "growth_factor": growth_factor,
    }


def build_suggestion_plan(
    goals: list[dict[str, Any]], analysis: dict[str, Any], age: int
) -> dict[str, Any]:
    ordered_goals = sorted(goals, key=lambda goal: (goal["years"], -goal["monthly_sip"]))
    priority = ordered_goals[0]
    status = analysis["status"]

    if status == "Achievable":
        focus = (
            f"Keep {priority['name']} as the first milestone because it arrives in "
            f"{priority['years']} years, then build the longer-term goals around it."
        )
        action = "Protect your emergency reserve and increase contributions whenever your income rises."
    elif status == "Challenging":
        focus = f"Focus first on {priority['name']} and close the small funding gap before adding more goals."
        action = "Increase the saving rate gradually, reduce flexible spending, or extend the nearest deadline."
    else:
        focus = f"Prioritize {priority['name']} and avoid funding every goal equally while the plan is highly challenging."
        action = "Choose one near-term goal, extend distant timelines, and raise savings in manageable steps."

    horizon_note = (
        "With a longer horizon, diversified growth assets can be considered after an emergency reserve is built."
        if age < 35
        else "Balance growth with stability as goals get closer, and review the plan at least once a year."
    )

    investment_options = [
        _investment_scenario(
            "Mutual funds", 12, "Diversified long-term growth", "Medium to high",
            "Consider broad, diversified funds for long horizons; returns are not guaranteed.",
            priority["future_cost"], priority["years"],
        ),
        _investment_scenario(
            "Fixed deposit (FD)", 6.5, "Capital stability and predictable interest", "Low to medium",
            "Useful for shorter horizons and stability; rates, tax, and early-withdrawal rules vary.",
            priority["future_cost"], priority["years"],
        ),
        _investment_scenario(
            "Gold", 7, "Diversifier and value hedge", "Medium",
            "Use as a limited diversifier rather than the only goal investment.",
            priority["future_cost"], priority["years"],
        ),
        _investment_scenario(
            "Stocks", 14, "Long-term growth potential", "High",
            "Use only for goals far away and diversify; avoid relying on one company.",
            priority["future_cost"], priority["years"],
        ),
        _investment_scenario(
            "Real estate", 9, "Large, long-term asset goal", "Medium to high",
            "Plan for down payment, liquidity, taxes, maintenance, and borrowing costs.",
            priority["future_cost"], priority["years"],
        ),
    ]
    equal_monthly_amount = priority["future_cost"] / sum(
        option["growth_factor"] for option in investment_options
    )
    for option in investment_options:
        option["monthly_amount"] = round(equal_monthly_amount, 2)
        option["yearly_amount"] = round(equal_monthly_amount * 12, 2)
        option["projected_value"] = round(equal_monthly_amount * option["growth_factor"], 2)
        option["projected_growth"] = round(
            option["projected_value"] - equal_monthly_amount * priority["years"] * 12, 2
        )
        option.pop("growth_factor")

    return {
        "priority_goal": priority["name"],
        "focus": focus,
        "action": action,
        "horizon_note": horizon_note,
        "steps": [
            f"Fund {priority['name']} first because its {priority['years']}-year timeline is the nearest.",
            "Keep at least three to six months of essential expenses in a liquid emergency reserve.",
            "Review the contribution amount yearly when salary, costs, or timelines change.",
        ],
        "investment_options": investment_options,
    }
