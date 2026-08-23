# 🚀 Parallel Execution Architecture & Design Idea

## 1. Overview
This document outlines the architectural specification for introducing multi-level parallel execution across Epics and Sprints, controlled via an environment variable (`MAX_PARALLEL_SPRINTS`).

---

## 2. Core Specifications

### A. Dynamic Concurrency Control
- **Environment Variable**: `MAX_PARALLEL_SPRINTS` (Default: `1`)
- **Behavior**: Controls the maximum number of worker threads/processes allocated for parallel Epic and Sprint execution.
- **Use Cases**:
  - `MAX_PARALLEL_SPRINTS=1`: Sequential, single-worker execution (Ideal for single local LLM / standard GPU setups).
  - `MAX_PARALLEL_SPRINTS=N` (e.g. `4`): Concurrent multi-worker execution (Ideal for multi-GPU, vLLM, or cloud API setups).

---

## 3. Two-Tier Parallel Dependency Resolution (DAG)

### Tier 1: Epic-Level Parallelism (Phase 1 Refinement)
During Phase 1 Overall Architecture Debate (`state/.evaluator/overall_debate_log.md`), Technical Architect analyzes Clean Architecture layer dependencies and assigns `depends_on_epics`:

```yaml
epics:
  - id: "epic_1_domain_core"
    depends_on: [] # No dependencies -> Ready for parallel execution
  - id: "epic_3_infrastructure_layer"
    depends_on: [] # No dependencies -> Can run in parallel with epic_1!
  - id: "epic_2_application_usecases"
    depends_on: ["epic_1_domain_core"] # Blocked until epic_1 completes
  - id: "epic_4_interface_adapters"
    depends_on: ["epic_1_domain_core", "epic_3_infrastructure_layer"]
```

### Tier 2: Task/File-Level Parallelism (Phase 2 Refinement)
During Phase 2 Epic Refinement (`sprint_1_backlog.yaml`), tasks are broken down by physical files (`[FILE] path/to/file.go`) with explicit `depends_on` task IDs:

```yaml
sprint: 1
epic: "Epic 3 Infrastructure Layer"
tasks:
  - id: "TASK-3.1"
    name: "[FILE] internal/infrastructure/adapter/md5_generator.go"
    depends_on: [] # Parallelizable
  - id: "TASK-3.2"
    name: "[FILE] internal/infrastructure/adapter/grid_rasterizer.go"
    depends_on: [] # Parallelizable alongside TASK-3.1
  - id: "TASK-3.3"
    name: "[FILE] internal/infrastructure/adapter/infrastructure_composite_test.go"
    depends_on: ["TASK-3.1", "TASK-3.2"] # Barrier block
```

---

## 4. Execution Engine Implementation Strategy (`ScrumRunner`)

```python
import os
from concurrent.futures import ThreadPoolExecutor

class ScrumRunner:
    def __init__(self, root_dir):
        self.max_workers = int(os.getenv("MAX_PARALLEL_SPRINTS", "1"))

    def execute_sprints(self, ready_tasks):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Dispatch independent tasks (depends_on: []) up to max_workers limit
            futures = [executor.submit(self.run_task, task) for task in ready_tasks]
            for future in futures:
                future.result()
```

---

## 5. Summary & Benefits
- **Zero Lock In**: Gracefully scales from 1 worker (local) to N workers (distributed).
- **Safe Graph Traversal**: Prevents race conditions by honoring Clean Architecture layer boundaries.
