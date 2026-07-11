"""v1 用户接口"""
from fastapi import APIRouter, Depends
from ....schemas.user import UserCreate, UserResponse
from ....core.deps import get_user_service, get_user_repository
from ....services.user_service import UserService
from ....repositories.user_repo import UserRepository

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return await service.register(user_in.username, user_in.email, user_in.password)


@router.get("/", response_model=list[UserResponse])
async def list_users(repo: UserRepository = Depends(get_user_repository)):
    return await repo.list()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return await service.get_user(user_id)
