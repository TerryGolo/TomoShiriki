# Journal Logging Rule

**Description:** A rule to ensure all significant work, changes, and decisions are logged in a journal file to maintain a historical record of the project's development.

## Instructions for the AI Assistant

Whenever you complete a significant task, feature implementation, refactoring, or bug fix, you must create or append an entry to the daily journal file located in the `docs/journal/` directory.

### Journal Entry Format
The file should be named with the current date, e.g., `docs/journal/YYYY-MM-DD.md`.
Please use the following format for each journal entry within the file:

```markdown
## Task: <Short Task Title>
- **Time:** <HH:MM>
- **Completed by:** AI Assistant
- **Files Modified:** `<list of files changed>`
- **Summary of Changes:** 
  - <bullet point 1>
  - <bullet point 2>
- **Reasoning/Notes:** <Any important design decisions or context>
```

### Process
1. Verify if `docs/journal/YYYY-MM-DD.md` exists for today's date. If it does not exist, create it with a top-level `# Journal - YYYY-MM-DD` heading.
2. Append the new entry at the end of the file.
3. Do not prompt the user for permission to log the journal entry; do it automatically as the final step of your task execution.
