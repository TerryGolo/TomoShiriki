# Ralph Loop: Agent Instructions & Skills

You are running inside an autonomous **Ralph Loop** designed to incrementally develop the **TomoShiriki** project. Your execution environment runs you repeatedly to complete a checklist of tasks. To succeed, follow these rules and guidelines.

---

## 1. Loop Workflow
In every iteration, you must perform the following steps:
1. **Read Progress**: Read `docs/tasks.md` to find the first incomplete task (e.g. `- [ ]`).
2. **Read PRD**: Read `docs/PRD.md` to understand the full context of the feature you need to implement.
3. **Write Code**: Implement the changes needed for the chosen task.
4. **Test & Verify**: Run tests (`python manage.py test`) to verify that your implementation works and doesn't break existing features.
5. **Mark Task Complete**: Update `docs/tasks.md` by changing the checkbox to `- [x]` for the task you completed.
6. **Commit**: Create a git commit with a message detailing what you did (e.g., `git commit -am "feat: implement booking status transition rules"`).
7. **Exit**: Exit the agent session cleanly so the loop shell script can start the next iteration.

---

## 2. Coding Guidelines
- **Maintain Exclusivity**: Respect the domain models. For example, a `Resource` must have exactly one owner (either `User` or `Community`), which is already enforced by the custom `clean()` validation. Maintain this integrity.
- **Write Modular Code**: Ensure code additions are clean and fit Django/DRF patterns. Keep serializers and models decoupled where appropriate.
- **Do Not Leave Placeholders**: Write fully functional, clean Python code.

---

## 3. Git Commits
- Make atomic commits representing one logical change.
- Make sure to add new files (like tests) using `git add` before committing.
- Commit messages should follow conventional commits format (e.g., `feat: ...`, `fix: ...`, `test: ...`).

---

## 4. Exit Criteria
- When all tasks in `docs/tasks.md` are marked complete (no `- [ ]` left), print a message like `All tasks completed!` and exit. The loop script will detect this and terminate.
