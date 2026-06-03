# Ralph Loop Tasks

This file tracks the status of the development tasks. The autonomous coding loop script checks for unchecked items (`- [ ]`) in this list and executes them one by one.

- [ ] Implement Resource Availability & Overlap Validation on Booking models/serializers
- [ ] Implement Booking Lifecycle Workflow Transition rules (restrict invalid status changes)
- [ ] Implement custom Django Signals for Plugin Hook System (booking created and status changed)
- [ ] Implement core unit tests in `core/tests.py` covering validations, workflows, and signals
- [ ] Verify test suite runs successfully with `python manage.py test`
