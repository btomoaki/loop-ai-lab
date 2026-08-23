# Task Management & Execution Rules

## 1. Synchronous Execution for Short Commands
- Short-running commands (e.g. `cat`, `ls`, `find`, `git status`, `pkill`, `python3 -c`) MUST be executed with sufficient `WaitMsBeforeAsync` (5000ms+) to complete synchronously.
- Do NOT spawn asynchronous background tasks for quick inspection or utility commands to prevent UI task clutter.

## 2. Autonomous Task Cleanup
- Any background tasks launched during a session must be automatically managed and cleaned up by the assistant without requiring user intervention or explicit "clean tasks" prompts.
- Before ending a turn, verify that no stale background tasks are left lingering.
