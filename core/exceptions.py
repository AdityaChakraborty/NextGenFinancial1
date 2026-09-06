from fastapi import HTTPException, status


class PlannerException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class InvalidCityException(PlannerException):
    def __init__(self, city: str):
        super().__init__(
            detail=f"City '{city}' not found in the reference dataset.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class InvalidGoalException(PlannerException):
    def __init__(self, goal: str):
        super().__init__(
            detail=f"Goal '{goal}' is not available in the reference dataset.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class UnrealisticGoalException(PlannerException):
    def __init__(self, message: str = "Goal timeline must be strictly positive."):
        super().__init__(detail=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class DataPipelineException(PlannerException):
    def __init__(self, message: str):
        super().__init__(detail=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvalidReferenceDataException(PlannerException):
    def __init__(self, message: str):
        super().__init__(detail=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
