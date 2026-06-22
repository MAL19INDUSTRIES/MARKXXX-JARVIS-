import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any
from memory.task_history import record_task


class TaskStatus(Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    COMPLETED  = "completed"
    FAILED     = "failed"
    CANCELLED  = "cancelled"


class TaskPriority(Enum):
    LOW    = 3
    NORMAL = 2
    HIGH   = 1   


@dataclass(order=True)
class Task:
    priority:    int                       
    created_at:  float = field(compare=False)
    task_id:     str   = field(compare=False)
    goal:        str   = field(compare=False)
    status:      TaskStatus = field(compare=False, default=TaskStatus.PENDING)
    result:      Any        = field(compare=False, default=None)
    error:       str        = field(compare=False, default="")
    speak:       Any        = field(compare=False, default=None)   
    on_complete: Any        = field(compare=False, default=None)  
    cancel_flag: threading.Event = field(compare=False, default_factory=threading.Event)


class TaskQueue:
    def __init__(self, max_concurrent: int = 2, awareness=None):
        self._queue:        list[Task]       = []
        self._lock:         threading.Lock   = threading.Lock()
        self._condition:    threading.Condition = threading.Condition(self._lock)
        self._tasks:        dict[str, Task]  = {} 
        self._running:      bool             = False
        self._worker_thread: threading.Thread | None = None
        self._max_concurrent = max_concurrent
        self._active_count   = 0
        self._executor       = None
        self._awareness      = awareness

    def _get_executor(self):
        if self._executor is None:
            from agent.executor import AgentExecutor
            self._executor = AgentExecutor(awareness=self._awareness)
        return self._executor

    def start(self) -> None:
        if self._running:
            return
        self._running      = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="AgentTaskQueue"
        )
        self._worker_thread.start()
        print("[TaskQueue] ✅ Started")

    def stop(self) -> None:
        self._running = False
        with self._condition:
            self._condition.notify_all()
        print("[TaskQueue] 🔴 Stopped")

    def submit(
        self,
        goal:        str,
        priority:    TaskPriority = TaskPriority.NORMAL,
        speak:       Callable | None = None,
        on_complete: Callable | None = None,
    ) -> str:

        task_id = str(uuid.uuid4())[:8]
        task    = Task(
            priority    = priority.value,
            created_at  = time.time(),
            task_id     = task_id,
            goal        = goal,
            speak       = speak,
            on_complete = on_complete,
        )

        with self._condition:
            self._queue.append(task)
            self._queue.sort(key=lambda t: (t.priority, t.created_at))
            self._tasks[task_id] = task
            self._condition.notify()

        print(f"[TaskQueue] 📥 Task queued: [{task_id}] {goal[:60]}")
        return task_id

    def cancel(self, task_id: str) -> bool:

        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False

            task.cancel_flag.set()
            task.status = TaskStatus.CANCELLED
            print(f"[TaskQueue] 🚫 Task cancelled: [{task_id}]")
            return True


    def cancel_running(self, *args, **kwargs):
        return False


    def get_status(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            return {
                "task_id": task.task_id,
                "goal":    task.goal,
                "status":  task.status.value,
                "result":  task.result,
                "error":   task.error,
            }

    def get_all_statuses(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "task_id": t.task_id,
                    "goal":    t.goal[:50],
                    "status":  t.status.value,
                }
                for t in self._tasks.values()
            ]

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._queue if t.status == TaskStatus.PENDING)

    def _worker_loop(self) -> None:
        while self._running:
            task = None

            with self._condition:
                while self._running and not self._next_task():
                    self._condition.wait(timeout=1.0)
                task = self._next_task()
                if task:
                    task.status = TaskStatus.RUNNING
                    self._active_count += 1
                    try:
                        self._queue.remove(task)
                    except ValueError:
                        pass

            if task:
                threading.Thread(
                    target=self._run_task,
                    args=(task,),
                    daemon=True,
                    name=f"AgentTask-{task.task_id}"
                ).start()

    def _next_task(self) -> Task | None:
        if self._active_count >= self._max_concurrent:
            return None
        for task in self._queue:
            if task.status == TaskStatus.PENDING and not task.cancel_flag.is_set():
                return task
        return None

    def _run_task(self, task: Task) -> None:
        print(f"[TaskQueue] ▶️ Running: [{task.task_id}] {task.goal[:60]}")
        try:
            executor = self._get_executor()
            result   = executor.execute(
                goal        = task.goal,
                speak       = task.speak,
                cancel_flag = task.cancel_flag,
            )

            step_results = getattr(executor, "last_step_results", {}) or {}
            if step_results:
                step_result_text = "\n".join(
                    f"Step {k}: {v}" for k, v in step_results.items()
                )
                task.result = f"{result}\n\nSTEP RESULTS:\n{step_result_text}"
            else:
                task.result = result

            with self._lock:
                if task.cancel_flag.is_set():
                    task.status = TaskStatus.CANCELLED
                else:
                    task.status = TaskStatus.COMPLETED
                    task.result = task.result or result
                self._active_count -= 1

            if task.on_complete and not task.cancel_flag.is_set():
                try:
                    task.on_complete(task.task_id, result)
                except Exception as e:
                    print(f"[TaskQueue] ⚠️ on_complete callback error: {e}")

            if not task.cancel_flag.is_set():
                completion_msg = f"Task completed: {task.goal[:90]}"

                # Push completion into awareness so UI/state knows it finished.
                if self._awareness:
                    try:
                        self._awareness.record_event(completion_msg)
                        self._awareness.clear_active_tool()
                    except Exception as e:
                        print(f"[TaskQueue] ⚠️ awareness completion update failed: {e}")

                # Tell the live assistant/user that the background task finished.
                if task.speak:
                    try:
                        task.speak(completion_msg)
                    except Exception as e:
                        print(f"[TaskQueue] ⚠️ speak completion notification failed: {e}")

            try:
                record_task(
                    task_id=task.task_id,
                    goal=task.goal,
                    status=task.status.value,
                    result=task.result,
                    error=task.error,
                )
            except Exception as e:
                print(f"[TaskQueue] ⚠️ task history save failed: {e}")

            print(f"[TaskQueue] ✅ Completed: [{task.task_id}]")

        except Exception as e:
            with self._lock:
                task.status = TaskStatus.FAILED
                task.error  = str(e)
                self._active_count -= 1

            failure_msg = f"Task failed: {task.goal[:90]} — {e}"

            if self._awareness:
                try:
                    self._awareness.record_event(failure_msg)
                    self._awareness.clear_active_tool()
                except Exception as ae:
                    print(f"[TaskQueue] ⚠️ awareness failure update failed: {ae}")

            if task.speak:
                try:
                    task.speak(failure_msg)
                except Exception as se:
                    print(f"[TaskQueue] ⚠️ speak failure notification failed: {se}")

            try:
                record_task(
                    task_id=task.task_id,
                    goal=task.goal,
                    status=task.status.value,
                    result=task.result,
                    error=task.error,
                )
            except Exception as he:
                print(f"[TaskQueue] ⚠️ task history save failed: {he}")

            print(f"[TaskQueue] ❌ Failed: [{task.task_id}] {e}")

        with self._condition:
            self._condition.notify()

_queue        = TaskQueue(max_concurrent=2)
_queue_started = False
_queue_lock    = threading.Lock()


def get_queue(awareness=None) -> TaskQueue:
    global _queue, _queue_started

    with _queue_lock:
        if awareness is not None and getattr(_queue, "_awareness", None) is None:
            _queue = TaskQueue(max_concurrent=2, awareness=awareness)
            _queue_started = False

        if not _queue_started:
            _queue.start()
            _queue_started = True

    return _queue