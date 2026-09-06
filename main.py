from pathlib import Path
import math

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

from services.calculator import FinancialEngine


BASE_DIR = Path(__file__).resolve().parent
engine = FinancialEngine(BASE_DIR / "city_goal_costs.csv")

app = FastAPI(
    title="Next Gen Financial",
    description="A local educational financial-planning simulation for future goals.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class GoalRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    current_cost: float = Field(gt=0, le=1_000_000_000)
    years: int = Field(gt=0, le=60)
    frequency: str = Field(default="monthly", pattern="^(monthly|yearly)$")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("current_cost")
    @classmethod
    def reject_non_finite_cost(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("must be a finite number")
        return value


class PlanRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=100)
    city: str = Field(min_length=1, max_length=100)
    salary: float = Field(ge=1_000, le=10_000_000)
    saving_percentage: float = Field(gt=0, le=100)
    inflation_rate: float = Field(gt=0, le=20, default=6)
    annual_return: float = Field(gt=0, le=30, default=12)
    goals: list[GoalRequest] = Field(min_length=1, max_length=12)

    @field_validator("name", "city", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("salary", "saving_percentage", "inflation_rate", "annual_return")
    @classmethod
    def reject_non_finite_numbers(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("must be a finite number")
        return value

    @model_validator(mode="after")
    def reject_duplicate_goals(self):
        names = [goal.name.casefold() for goal in self.goals]
        if len(names) != len(set(names)):
            raise ValueError("goal names must be unique")
        return self


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"] if part != "body")
        errors.append({"field": location or "request", "message": error["msg"]})
    return JSONResponse(status_code=422, content={"detail": "Please correct the highlighted fields.", "errors": errors})


def calculate_goal(city: str, goal: str, years: int) -> dict[str, float]:
    current_cost = engine.get_current_cost(goal=goal, city=city)
    future_cost = engine.calculate_future_cost(current_cost, years)
    monthly_investment = engine.required_monthly_investment(future_cost, years)
    return {
        "current_cost": round(current_cost, 2),
        "future_cost": round(future_cost, 2),
        "monthly_sip": round(monthly_investment, 2),
    }


def calculate_selected_goal(
    goal: GoalRequest, inflation_rate: float, annual_return: float
) -> dict[str, float | str | int]:
    future_cost = goal.current_cost * (1 + inflation_rate / 100) ** goal.years
    monthly_rate = annual_return / 100 / 12
    months = goal.years * 12
    monthly_investment = (future_cost * monthly_rate) / ((1 + monthly_rate) ** months - 1)
    return {
        "name": goal.name,
        "years": goal.years,
        "frequency": goal.frequency,
        "current_cost": round(goal.current_cost, 2),
        "future_cost": round(future_cost, 2),
        "monthly_sip": round(monthly_investment, 2),
        "yearly_investment": round(monthly_investment * 12, 2),
        "contribution_amount": round(
            monthly_investment if goal.frequency == "monthly" else monthly_investment * 12,
            2,
        ),
    }


@app.get("/")
async def frontend() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/cities")
async def list_cities() -> list[str]:
    return sorted(engine.city_data["City"].dropna().astype(str).unique().tolist())


@app.get("/api/v1/default-goals")
async def default_goals(city: str) -> list[dict[str, str | float]]:
    return [
        {"name": "Marriage", "current_cost": engine.get_current_cost(city, "Marriage")},
        {"name": "Home", "current_cost": engine.get_current_cost(city, "Home")},
        {"name": "Education", "current_cost": 500000},
        {"name": "Vacation / Trip", "current_cost": 200000},
        {"name": "Car / Bike", "current_cost": engine.get_current_cost(city, "Car")},
    ]


@app.post("/api/v1/plan")
async def generate_plan(request: PlanRequest):
    goal_values = [
        calculate_selected_goal(goal, request.inflation_rate, request.annual_return)
        for goal in request.goals
    ]
    total_monthly_investment = sum(goal["monthly_sip"] for goal in goal_values)

    return {
        "user": request.name,
        "age": request.age,
        "city": request.city,
        "goals": goal_values,
        "assumptions": {
            "inflation_rate": request.inflation_rate,
            "annual_return": request.annual_return,
            "area_type": "Central",
        },
        "analysis": engine.feasibility_analysis(
            request.salary, request.saving_percentage, total_monthly_investment
        ),
    }
