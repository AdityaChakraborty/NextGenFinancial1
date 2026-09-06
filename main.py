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
    title="Financial Dream Planner",
    description="A local educational financial-planning simulation for future goals.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class CustomGoal(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    current_cost: float = Field(gt=0)
    years: int = Field(gt=0, le=60)

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
    salary: float = Field(gt=0)
    saving_percentage: float = Field(gt=0, le=100)
    years_to_marriage: int = Field(gt=0, le=60)
    years_to_car: int = Field(gt=0, le=60)
    years_to_home: int = Field(gt=0, le=60)
    custom_goals: list[CustomGoal] = Field(default_factory=list, max_length=8)

    @field_validator("name", "city", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("salary", "saving_percentage")
    @classmethod
    def reject_non_finite_numbers(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("must be a finite number")
        return value

    @model_validator(mode="after")
    def reject_duplicate_custom_goals(self):
        names = [goal.name.casefold() for goal in self.custom_goals]
        if len(names) != len(set(names)):
            raise ValueError("custom goal names must be unique")
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


def calculate_custom_goal(goal: CustomGoal) -> dict[str, float | str | int]:
    future_cost = engine.calculate_future_cost(goal.current_cost, goal.years)
    monthly_investment = engine.required_monthly_investment(future_cost, goal.years)
    return {
        "name": goal.name,
        "years": goal.years,
        "current_cost": round(goal.current_cost, 2),
        "future_cost": round(future_cost, 2),
        "monthly_sip": round(monthly_investment, 2),
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


@app.post("/api/v1/plan")
async def generate_plan(request: PlanRequest):
    marriage = calculate_goal(request.city, "Marriage", request.years_to_marriage)
    car = calculate_goal(request.city, "Car", request.years_to_car)
    home = calculate_goal(request.city, "Home", request.years_to_home)
    custom_goals = [calculate_custom_goal(goal) for goal in request.custom_goals]
    goal_values = [marriage, car, home, *custom_goals]
    total_monthly_investment = sum(goal["monthly_sip"] for goal in goal_values)

    return {
        "user": request.name,
        "age": request.age,
        "city": request.city,
        "goals": {"marriage": marriage, "car": car, "home": home},
        "custom_goals": custom_goals,
        "assumptions": {
            "inflation_rate": engine.INFLATION_RATE,
            "annual_return": engine.ANNUAL_RETURN,
            "area_type": "Central",
        },
        "analysis": engine.feasibility_analysis(
            request.salary, request.saving_percentage, total_monthly_investment
        ),
    }
