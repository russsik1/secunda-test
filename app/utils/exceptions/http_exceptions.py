from fastapi import HTTPException, status


def INVALID_API_KEY() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


def ORGANIZATION_NOT_FOUND(organization_id: int | None = None) -> HTTPException:
    if organization_id is None:
        detail = "Organization not found"
    else:
        detail = f"Organization {organization_id} not found"
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def DATABASE_ERROR() -> HTTPException:
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")


def INTERNAL_SERVER_ERROR() -> HTTPException:
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

