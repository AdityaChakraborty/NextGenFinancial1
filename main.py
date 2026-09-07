from pathlib import Path
import math
import re
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

from services.calculator import FinancialEngine
from services.recommendations import build_suggestion_plan
from ml_models.salary_predictor import predict_salary


BASE_DIR = Path(__file__).resolve().parent
engine = FinancialEngine(BASE_DIR / "city_goal_costs.csv")
MODEL_ARTIFACT = BASE_DIR / "artifacts" / "salary_predictor.joblib"

app = FastAPI(
    title="Next Gen Financial",
    description="A local educational financial-planning simulation for future goals.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class GoalRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    current_cost: float = Field(ge=1_000, le=1_000_000_000)
    years: int = Field(gt=0, le=60)
    frequency: str = Field(default="monthly", pattern="^(monthly|yearly)$")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("must contain at least one letter")
        return value

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
    education: str = Field(min_length=1, max_length=100)
    job_role: str = Field(min_length=1, max_length=100)
    goals: list[GoalRequest] = Field(min_length=1, max_length=12)

    @field_validator("name", "city", "education", "job_role", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        value = value.strip()
        if value and not re.search(r"[A-Za-z]", value):
            raise ValueError("must contain at least one letter")
        return value

    @field_validator("name")
    @classmethod
    def validate_person_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z]+(?:[ .'-][A-Za-z]+)*", value):
            raise ValueError("use letters, spaces, apostrophes, periods, or hyphens only")
        return value

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


class SalaryPredictionRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    education: str = Field(min_length=1, max_length=100)
    job_role: str = Field(min_length=1, max_length=100)

    @field_validator("city", "education", "job_role", mode="before")
    @classmethod
    def strip_profile_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


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
        {"name": "Emergency Fund", "current_cost": 300000},
    ]


@app.get("/api/v1/ml/status")
async def ml_status() -> dict[str, Any]:
    if not MODEL_ARTIFACT.exists():
        return {"available": False, "message": "Run python train_model.py to create the local model."}
    import joblib

    artifact = joblib.load(MODEL_ARTIFACT)
    return {
        "available": True,
        "selected_model": artifact["selected_model"],
        "features": artifact["features"],
        "data_report": artifact["data_report"],
        "reports": artifact["reports"],
    }


@app.post("/api/v1/ml/predict-salary")
async def predict_salary_endpoint(request: SalaryPredictionRequest) -> dict[str, Any]:
    if not MODEL_ARTIFACT.exists():
        return JSONResponse(
            status_code=503,
            content={"detail": "Local model is not trained. Run python train_model.py first."},
        )
    return predict_salary(
        MODEL_ARTIFACT,
        {"City": request.city, "Education": request.education, "Job_Role": request.job_role},
    )


@app.post("/api/v1/plan")
async def generate_plan(request: PlanRequest):
    goal_values = [
        calculate_selected_goal(goal, request.inflation_rate, request.annual_return)
        for goal in request.goals
    ]
    total_monthly_investment = sum(goal["monthly_sip"] for goal in goal_values)
    profile_salary = request.salary
    if MODEL_ARTIFACT.exists():
        salary_prediction = predict_salary(
            MODEL_ARTIFACT,
            {"City": request.city, "Education": request.education, "Job_Role": request.job_role},
        )
        profile_salary = salary_prediction["predicted_monthly_salary"]
    analysis = engine.feasibility_analysis(
        profile_salary, request.saving_percentage, total_monthly_investment
    )
    suggestion_plan = build_suggestion_plan(goal_values, analysis, request.age)
    if MODEL_ARTIFACT.exists():
        suggestion_plan["model_insight"] = {"available": True, **salary_prediction}
    else:
        suggestion_plan["model_insight"] = {
            "available": False,
            "message": "The trained salary model is unavailable, so the entered salary is used.",
        }

    return {
        "user": request.name,
        "age": request.age,
        "city": request.city,
        "education": request.education,
        "job_role": request.job_role,
        "calculation_profile": {
            "monthly_salary_used": round(profile_salary, 2),
            "salary_source": "profile prediction" if MODEL_ARTIFACT.exists() else "entered salary fallback",
        },
        "goals": goal_values,
        "assumptions": {
            "inflation_rate": request.inflation_rate,
            "annual_return": request.annual_return,
            "area_type": "Central",
        },
        "analysis": analysis,
        "suggestion_plan": suggestion_plan,
    }
