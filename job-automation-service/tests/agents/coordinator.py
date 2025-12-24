"""Agent coordinator for multi-agent task management."""

import asyncio
import logging
import json
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import SessionLocal
from app.models.agent_task import AgentTask
from tests.agents.lock_manager import DatabaseLock
from tests.agents.config import config

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentType(str, Enum):
    """Agent types for capability-based coordination."""
    SCRAPER_TEST = "scraper_test"
    MATCHER_TEST = "matcher_test"
    API_TEST = "api_test"
    COVER_LETTER_TEST = "cover_letter_test"
    SCHEDULER_TEST = "scheduler_test"
    GAP_ANALYSIS = "gap_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    DOC_ANALYSIS = "doc_analysis"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    INTEGRATION_TEST = "integration_test"
    PERFORMANCE_BENCHMARK = "performance_benchmark"
    REGRESSION_TEST = "regression_test"


class AgentCoordinator:
    """Coordinates multiple agents with deterministic task management."""
    
    def __init__(self, max_parallel: int = None):
        """Initialize coordinator.
        
        Args:
            max_parallel: Maximum parallel agents (defaults to config)
        """
        self.max_parallel = max_parallel or config.max_parallel_agents
        self.agents: Dict[AgentType, Callable] = {}
        self.running_agents: Dict[str, asyncio.Task] = {}
        self.status_file = config.status_file
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized coordinator with max_parallel={self.max_parallel}")
    
    def register_agent(self, agent_type: AgentType, agent_func: Callable):
        """Register an agent function.
        
        Args:
            agent_type: Type of agent
            agent_func: Async function that takes a Task and returns results
        """
        self.agents[agent_type] = agent_func
        logger.debug(f"Registered agent: {agent_type.value}")
    
    def add_task(
        self,
        task_id: str,
        agent_type: AgentType,
        description: str,
        dependencies: List[str] = None,
        priority: int = 0,
        timeout: int = None
    ):
        """Add a task to the queue.
        
        Args:
            task_id: Unique task identifier
            agent_type: Type of agent to run
            description: Task description
            dependencies: List of task IDs this depends on
            priority: Task priority (higher = more important)
            timeout: Task timeout in seconds
        """
        db = SessionLocal()
        try:
            # Check if task already exists
            existing = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            
            if existing:
                logger.warning(f"Task {task_id} already exists, updating")
                existing.agent_type = agent_type.value
                existing.description = description
                existing.dependencies = dependencies or []
                existing.priority = priority
                existing.timeout = timeout or config.default_task_timeout
                existing.status = TaskStatus.PENDING.value
            else:
                task = AgentTask(
                    id=task_id,
                    agent_type=agent_type.value,
                    description=description,
                    status=TaskStatus.PENDING.value,
                    priority=priority,
                    dependencies=dependencies or [],
                    timeout=timeout or config.default_task_timeout
                )
                db.add(task)
            
            db.commit()
            logger.info(f"Added task: {task_id} ({agent_type.value})")
        except Exception as e:
            logger.error(f"Error adding task {task_id}: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _get_task(self, task_id: str, db: Session) -> Optional[AgentTask]:
        """Get task from database."""
        return db.query(AgentTask).filter(AgentTask.id == task_id).first()
    
    def _can_run(self, task: AgentTask, db: Session) -> bool:
        """Check if task dependencies are met.
        
        Args:
            task: Task to check
            db: Database session
            
        Returns:
            True if task can run
        """
        if task.status != TaskStatus.PENDING.value:
            return False
        
        # Check dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                dep_task = db.query(AgentTask).filter(AgentTask.id == dep_id).first()
                if not dep_task:
                    logger.warning(f"Dependency {dep_id} not found for task {task.id}")
                    return False
                if dep_task.status != TaskStatus.COMPLETED.value:
                    return False
        
        return True
    
    def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        db: Session,
        error: str = None,
        result: Dict[str, Any] = None
    ):
        """Update task status in database."""
        task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if task:
            task.status = status.value
            task.updated_at = datetime.utcnow()
            
            if status == TaskStatus.IN_PROGRESS:
                task.started_at = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.utcnow()
                if result:
                    task.result = result
                if error:
                    task.error = error
            
            db.commit()
    
    def _save_status_file(self):
        """Save task status to file for external monitoring."""
        db = SessionLocal()
        try:
            tasks = db.query(AgentTask).all()
            status = {
                task.id: {
                    "status": task.status,
                    "agent_type": task.agent_type,
                    "assigned_agent": task.assigned_agent,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "priority": task.priority,
                }
                for task in tasks
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving status file: {e}")
        finally:
            db.close()
    
    async def run_agents(self):
        """Run agents in parallel with coordination."""
        logger.info("Starting agent execution")
        
        db = SessionLocal()
        try:
            # Get all pending tasks
            pending_tasks = db.query(AgentTask).filter(
                AgentTask.status == TaskStatus.PENDING.value
            ).order_by(AgentTask.priority.desc()).all()
            
            if not pending_tasks:
                logger.info("No pending tasks found")
                return
            
            logger.info(f"Found {len(pending_tasks)} pending tasks")
        finally:
            db.close()
        
        # Main execution loop
        iteration = 0
        max_iterations = 1000  # Safety limit
        
        while iteration < max_iterations:
            iteration += 1
            
            # Find runnable tasks
            runnable = self._get_runnable_tasks()
            
            # Start new agents if we have capacity
            while len(self.running_agents) < self.max_parallel and runnable:
                task = runnable.pop(0)
                await self._start_agent(task)
            
            # If no running agents and no runnable tasks, we're done
            if not self.running_agents and not runnable:
                # Check if there are any remaining pending tasks (might be blocked)
                db = SessionLocal()
                try:
                    remaining = db.query(AgentTask).filter(
                        AgentTask.status == TaskStatus.PENDING.value
                    ).count()
                    
                    if remaining > 0:
                        logger.warning(f"{remaining} tasks still pending (may be blocked)")
                        # Mark as blocked
                        blocked = db.query(AgentTask).filter(
                            and_(
                                AgentTask.status == TaskStatus.PENDING.value,
                                AgentTask.updated_at < datetime.utcnow() - timedelta(minutes=10)
                            )
                        ).all()
                        for task in blocked:
                            task.status = TaskStatus.BLOCKED.value
                        db.commit()
                finally:
                    db.close()
                break
            
            # Wait for at least one agent to complete
            if self.running_agents:
                done, pending = await asyncio.wait(
                    self.running_agents.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Remove completed tasks
                for task_id, agent_task in list(self.running_agents.items()):
                    if agent_task in done:
                        del self.running_agents[task_id]
                        try:
                            await agent_task  # Get result/exception
                        except Exception as e:
                            logger.error(f"Agent task {task_id} failed: {e}")
            
            # Small delay to prevent tight loop
            await asyncio.sleep(0.1)
        
        if iteration >= max_iterations:
            logger.error("Max iterations reached, stopping coordinator")
        
        logger.info("Agent execution completed")
        self._save_status_file()
    
    def _get_runnable_tasks(self) -> List[AgentTask]:
        """Get list of tasks that can run."""
        db = SessionLocal()
        try:
            pending = db.query(AgentTask).filter(
                AgentTask.status == TaskStatus.PENDING.value
            ).order_by(AgentTask.priority.desc()).all()
            
            runnable = []
            for task in pending:
                if self._can_run(task, db) and task.id not in self.running_agents:
                    runnable.append(task)
            
            return runnable
        finally:
            db.close()
    
    async def _start_agent(self, task: AgentTask):
        """Start an agent for a task."""
        agent_func = self.agents.get(AgentType(task.agent_type))
        
        if not agent_func:
            logger.error(f"No agent registered for type: {task.agent_type}")
            db = SessionLocal()
            try:
                self._update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    db,
                    error=f"No agent for {task.agent_type}"
                )
            finally:
                db.close()
            return
        
        # Create agent task
        agent_task = asyncio.create_task(
            self._run_agent(task, agent_func)
        )
        self.running_agents[task.id] = agent_task
        logger.info(f"Started agent for task: {task.id}")
    
    async def _run_agent(self, task: AgentTask, agent_func: Callable):
        """Run a single agent with locking."""
        agent_id = f"agent-{task.agent_type}-{task.id[:8]}"
        db = SessionLocal()
        
        try:
            # Update status to IN_PROGRESS
            self._update_task_status(task.id, TaskStatus.IN_PROGRESS, db)
            task.assigned_agent = agent_id
            db.commit()
            
            # Acquire lock
            with DatabaseLock(task.id, agent_id, timeout=task.timeout):
                logger.info(f"Running agent {agent_id} for task {task.id}")
                
                # Run agent function with retry logic
                max_retries = 2
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        result = await agent_func(task)
                        
                        # Update status to COMPLETED
                        self._update_task_status(
                            task.id,
                            TaskStatus.COMPLETED,
                            db,
                            result=result
                        )
                        logger.info(f"Task {task.id} completed successfully")
                        return  # Success, exit retry loop
                        
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries:
                            logger.warning(f"Agent {agent_id} attempt {attempt + 1} failed, retrying: {e}")
                            await asyncio.sleep(1)  # Wait before retry
                        else:
                            logger.error(f"Agent {agent_id} failed for task {task.id} after {max_retries + 1} attempts: {e}", exc_info=True)
                            self._update_task_status(
                                task.id,
                                TaskStatus.FAILED,
                                db,
                                error=f"Failed after {max_retries + 1} attempts: {str(e)}"
                            )
                            raise
        
        except TimeoutError as e:
            logger.error(f"Lock timeout for task {task.id}: {e}")
            self._update_task_status(
                task.id,
                TaskStatus.FAILED,
                db,
                error=f"Lock timeout: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error running agent for task {task.id}: {e}", exc_info=True)
            if not db.query(AgentTask).filter(AgentTask.id == task.id).first().status == TaskStatus.FAILED.value:
                self._update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    db,
                    error=str(e)
                )
        finally:
            db.close()
            self._save_status_file()

