from typing import Any


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
        focus = (
            f"Focus first on {priority['name']} and close the small funding gap before adding more goals."
        )
        action = "Increase the saving rate gradually, reduce flexible spending, or extend the nearest deadline."
    else:
        focus = (
            f"Prioritize {priority['name']} and avoid funding every goal equally while the plan is highly challenging."
        )
        action = "Choose one near-term goal, extend distant timelines, and raise savings in manageable steps."

    horizon_note = (
        "With a longer horizon, diversified growth assets can be considered after an emergency reserve is built."
        if age < 35
        else "Balance growth with stability as goals get closer, and review the plan at least once a year."
    )

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
        "investment_options": [
            {
                "name": "Mutual funds",
                "fit": "Diversified long-term growth",
                "risk": "Medium to high",
                "note": "Consider broad, diversified funds for long horizons; returns are not guaranteed.",
            },
            {
                "name": "Gold",
                "fit": "Diversifier and value hedge",
                "risk": "Medium",
                "note": "Use as a limited diversifier rather than the only goal investment.",
            },
            {
                "name": "Stocks",
                "fit": "Long-term growth potential",
                "risk": "High",
                "note": "Use only for goals far away and diversify; avoid relying on one company.",
            },
            {
                "name": "Real estate",
                "fit": "Large, long-term asset goal",
                "risk": "Medium to high",
                "note": "Plan for down payment, liquidity, taxes, maintenance, and borrowing costs.",
            },
        ],
    }
