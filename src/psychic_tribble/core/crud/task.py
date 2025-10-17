from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.psychic_tribble.models.task import Task
from src.psychic_tribble.schemas.task import TaskCreate, TaskUpdate
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException

async def create_task(db: AsyncSession, owner_id: int, task_in: TaskCreate) -> Task:
    try:
       task_in.model_dump(exclude_none=True), owner_id=owner_id)
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Task creation failed: duplicate or constraint violation")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")

async def get_tasks_for_user(db: AsyncSession, owner_id: int) -> list[Task]:
    result = await db.execute(select(Task).where(Task.owner_id == owner_id).order_by(Task.due_date))
    return result.scalars().all()

async def get_task_for_user(db: AsyncSession, task_id: int, owner_id: int) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == owner_id))
    return result.scalars().first()

async def update_task(db: AsyncSession, task: Task, task_in: TaskUpdate) -> Task:
    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task

async def delete_task(db: AsyncSession, task: Task) -> None:
    try:
        await db.delete(task)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
