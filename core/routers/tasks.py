from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.psychic_tribble.schemas.task import TaskCreate, TaskOut, TaskUpdate
from src.psychic_tribble.crud.task import create_task, get_tasks_for_user, get_task_for_user, update_task, delete_task
from src.psychic_tribble.dependencies import get_db, get_current_user

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_new_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    task = await create_task(db, user.id, task_in)
    return task

@router.get("/", response_model=list[TaskOut])
async def list_tasks(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    return await get_tasks_for_user(db, user.id)

@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    task = await get_task_for_user(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskOut)
async def modify_task(task_id: int, task_in: TaskUpdate, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    task = await get_task_for_user(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return await update_task(db, task, task_in)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(task_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    task = await get_task_for_user(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await delete_task(db, task)
