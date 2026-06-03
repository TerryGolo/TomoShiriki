# Product Requirements Document (PRD): TomoShiriki Core Features

## 1. Project Overview
**TomoShiriki** is a community-driven resource sharing framework built on Django. Its goal is to make it easy for physical and virtual communities to manage, lend, and borrow resources.

---

## 2. Current State
As of June 2026, the project consists of the following components:
- **Framework**: Django 6.0 + Django REST Framework (DRF).
- **Database**: SQLite for local development.
- **Models (`core/models.py`)**:
  - `User`: Extension of `AbstractUser` for authentication and profile management.
  - `Community`: Represents a boundary of resource sharing containing users.
  - `Resource`: Represents physical/virtual items. Enforces exclusive ownership (either a single user OR a single community owns it, not both, not neither).
  - `Booking`: Tracks resource borrowing lifecycle with statuses: `PENDING`, `APPROVED`, `REJECTED`, `COMPLETED`, `CANCELLED`.
- **API (`core/serializers.py`, `core/viewsets.py`, `tomoshiriki/urls.py`)**:
  - CRUD viewsets exposed at `/api/users/`, `/api/communities/`, `/api/resources/`, and `/api/bookings/`.
- **Admin**: All models registered in Django Admin at `/admin/`.

---

## 3. Scope of Work (Features to Develop)
To evolve TomoShiriki from a basic database schema into a production-ready framework, the following features must be implemented:

### Feature 1: Resource Availability & Overlap Validation
- **Requirement**: Prevent resources from being booked for overlapping time frames.
- **Rules**:
  - A booking can only be created or marked as `APPROVED` if there is no other `APPROVED` or `PENDING` booking for the same resource during the same time interval.
  - Cancelled or Rejected bookings do not count as overlaps.

### Feature 2: Booking Lifecycle & Workflow Transitions
- **Requirement**: Enforce valid status transitions.
- **Rules**:
  - Initial state is `PENDING`.
  - From `PENDING`, transition can go to `APPROVED` or `REJECTED`.
  - From `APPROVED`, transition can go to `COMPLETED` or `CANCELLED`.
  - A borrower should only be allowed to transition their own booking to `CANCELLED`.
  - The resource owner (or community admin) is the only one who can transition a booking to `APPROVED`, `REJECTED`, or `COMPLETED`.

### Feature 3: Plugin / Hook System
- **Requirement**: Allow third-party apps to hook into key lifecycle events.
- **Rules**:
  - Define custom Django Signals (e.g., `booking_created`, `booking_status_changed`, `resource_created`).
  - Allow plugin apps to register signal receivers to implement side effects like sending notifications, logging audits, or executing custom billing logic.

### Feature 4: Comprehensive Test Suite
- **Requirement**: Implement unit and integration tests in `core/tests.py`.
- **Test Cases**:
  - Resource validation (exclusivity of user/community owner).
  - Booking overlap validation.
  - Booking status transition restrictions.
  - Hook signal dispatching verification.
