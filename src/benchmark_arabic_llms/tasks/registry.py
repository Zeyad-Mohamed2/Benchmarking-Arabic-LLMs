"""Task registry providing plug-and-play task registration and discovery."""

from typing import Dict, Type, List
from benchmark_arabic_llms.tasks.base import BaseTask


class TaskRegistry:
    """Central registry for all benchmark tasks."""

    _registry: Dict[str, Type[BaseTask]] = {}
    _instances: Dict[str, BaseTask] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a task class under a specific identifier."""
        def decorator(task_cls: Type[BaseTask]):
            task_name = name.lower()
            cls._registry[task_name] = task_cls
            task_cls.name = task_name
            return task_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> BaseTask:
        """Get or instantiate a task by name."""
        task_name = str(name).lower()
        if task_name not in cls._instances:
            if task_name not in cls._registry:
                raise ValueError(
                    f"Unknown task: '{name}'. Available tasks: {cls.list_names()}"
                )
            cls._instances[task_name] = cls._registry[task_name]()
        return cls._instances[task_name]

    @classmethod
    def list_names(cls) -> List[str]:
        """Return names of all registered tasks."""
        return sorted(list(cls._registry.keys()))

    @classmethod
    def list_tasks(cls) -> List[BaseTask]:
        """Return instances of all registered tasks."""
        return [cls.get(name) for name in cls.list_names()]

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a task is registered."""
        return str(name).lower() in cls._registry


register_task = TaskRegistry.register
