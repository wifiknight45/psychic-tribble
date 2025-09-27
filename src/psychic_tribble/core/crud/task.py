from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.psychic_tribble.models.task import Task
from src.psychic_tribble.schemas.task import TaskCreate, TaskUpdate

async def create_task(db: AsyncSession, owner_id: int, task_in: TaskCreate) -> Task:
    task = Task(**task_in.dict(exclude_none=True), owner_id=owner_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

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
    await db.delete(task)
    await db.commit()
