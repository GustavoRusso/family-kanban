# Agent operating instructions

This file is the single entry point for every coding agent.


Humans use [README.md](README.md) for a short product introduction.

Product specification: [_docs/plan.md](_docs/plan.md).


## Git renames

When you rename or move a tracked file, always use `git mv <old> <new>` (not a plain filesystem rename or delete+add). That keeps Git history linked to the new path. After `git mv`, update all references to the old path in the same change.

## Architecture

Centralize every backend call in one services layer, and create a mock implementation of it so the whole app runs without a real backend.

Add tests.