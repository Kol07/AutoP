from fastapi import APIRouter

router = APIRouter(
    prefix = "/article",
    tags = ["Articles Flow"]
)

@router.get("/embed")
def embedArticle_route():
    
    return