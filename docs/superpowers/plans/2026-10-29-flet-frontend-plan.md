# Flet Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the minimal Flet window with a resilient dashboard that invokes existing `brain.py` functions without modifying `brain.py`.

**Architecture:** Keep all UI and defensive import logic in `main.py`. Load `brain.py` lazily, expose grouped action cards for Database, Laravel, Git, and Frontend operations, and report results in an in-app activity log. No new backend or API layer is introduced.

**Tech Stack:** Python 3, Flet, standard library (`importlib`, `traceback`, `datetime`).

**Spec:** Approved inline design from 2026-10-29: option 1, direct Flet frontend in `main.py`, `brain.py` unchanged.

## Global Constraints

- Do not edit `brain.py`.
- Preserve the existing Flet entry point in `main.py`.
- Keep the UI usable when `brain.py` cannot import because of missing dependencies or configuration.
- Do not execute arbitrary shell commands from user-entered fields.

## Review Focus

- `brain.py` import failure: show a visible unavailable state and keep the window usable; test with a mocked import failure.
- Empty required fields: block the action and log a readable validation message; test one action per group.
- Exceptions from a brain function: catch and log the exception without closing the app; test with a raising callable.
- `brain.py` unchanged: verify its git diff is empty after implementation.
- Long activity output: keep the log bounded and readable; test repeated events.

### Task 1: Build resilient brain loader and activity log

**Files:**
- Modify: `main.py`
- Test: manual smoke checks plus `python -m py_compile main.py`

**Interfaces:**
- Produces `load_brain()` returning the imported module or `None`.
- Produces `run_action(label, callback, *args, **kwargs)` that logs success/failure.

- [ ] Add lazy import handling and a status banner that distinguishes available, unavailable, and action-error states.
- [ ] Add a bounded in-memory activity log rendered in the page.
- [ ] Run `python -m py_compile main.py`.

### Task 2: Add dashboard layout and action cards

**Files:**
- Modify: `main.py`

**Interfaces:**
- Consumes `load_brain()` and `run_action()` from Task 1.
- Produces a Flet page with navigation rail/sections for Database, Laravel, Git, and Frontend.

- [ ] Add responsive dark dashboard styling, header, status indicator, and activity panel.
- [ ] Add validated forms for existing operations: database query/index/insert, Laravel project/CRUD, Git commit/fetch/pull, and frontend package/run.
- [ ] Wire each button only to named functions already present in `brain.py`.

### Task 3: Verify behavior and protect the untouched backend

**Files:**
- Modify: none beyond `main.py`

- [ ] Run `python -m py_compile main.py`.
- [ ] Run a no-window import/AST smoke check that confirms the UI module imports without executing `brain.py` eagerly.
- [ ] Compare `git diff -- brain.py` and confirm no changes.
- [ ] Launch the Flet app manually and verify the unavailable state and disabled-safe behavior when backend dependencies are absent.
