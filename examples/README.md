# TomoShiriki Seeding Scenarios Guide

This guide walks you through using the custom Django management command to seed mock data into the **TomoShiriki** resource sharing platform. The seeder is useful for demonstrations, manual testing, and automated validations.

---

## Getting Started

To run the seeding command, make sure your virtual environment is active, then use:

```bash
# Seed the default basic scenario
python manage.py seed_data --scenario basic

# Clear the database before seeding (recommended for a clean state)
python manage.py seed_data --scenario basic --clear
```

---

## Available Scenarios

### 1. Basic Scenario (`--scenario basic`)
Sets up a minimal viable setup with standard users, a single community, and a few pending or approved bookings.

* **Seeded Entities:**
  * **Users:** `admin_user` (superuser), `alice`, `bob`, `charlie`.
  * **Community:** "Greenwood Community Share" (with `alice`, `bob`, and `charlie` as members).
  * **Resources:**
    * "Electric Lawnmower" (owned by Greenwood Community Share)
    * "Cordless Drill" (owned by Greenwood Community Share)
    * "Alice's Cargo Trailer" (owned by `alice`)
  * **Bookings:**
    * `bob` books "Electric Lawnmower" for tomorrow (Status: `PENDING`)
    * `bob` books "Cordless Drill" for 2 days from now (Status: `APPROVED`)
    * `charlie` books "Alice's Cargo Trailer" for 3 days from now (Status: `PENDING`)

* **Execution:**
  ```bash
  python manage.py seed_data --scenario basic --clear
  ```

---

### 2. Workflow Scenario (`--scenario workflow`)
Sets up a database history demonstrating bookings at each possible status in the lifecycle transition workflow.

* **Seeded Entities:**
  * Same users and resources as the `basic` scenario.
  * **Bookings:**
    * **Pending:** `bob` books "Electric Lawnmower" (Starts tomorrow)
    * **Approved:** `bob` books "Cordless Drill" (Starts in 2 days)
    * **Rejected:** `charlie` books "Electric Lawnmower" (Starts tomorrow; conflicts with bob's pending booking, which is allowed because REJECTED status does not block overlaps)
    * **Completed:** `bob` books "Alice's Cargo Trailer" (In the past)
    * **Cancelled:** `charlie` books "Cordless Drill" (Starts in 3 days; cancelled by charlie)

* **Execution:**
  ```bash
  python manage.py seed_data --scenario workflow --clear
  ```

---

### 3. Overlap Scenario (`--scenario overlap`)
Demonstrates and validates the overlap prevention rules. It seeds multiple allowed overlapping bookings (e.g. cancelled/rejected bookings that occupy the same slot as an approved booking) and programmatically shows that attempting to insert a conflicting active booking is blocked by the model validations.

* **Seeded Entities:**
  * Same users and resources.
  * **Bookings:**
    * **Approved Booking:** `bob` books "Electric Lawnmower" for tomorrow 10:00 AM - 2:00 PM.
    * **Cancelled Booking:** `alice` books "Electric Lawnmower" tomorrow 11:00 AM - 1:00 PM (Succeeds because it is `CANCELLED`).
    * **Rejected Booking:** `charlie` books "Electric Lawnmower" tomorrow 12:00 PM - 2:00 PM (Succeeds because it is `REJECTED`).
  * **Conflict Demo:**
    * The command automatically attempts to create a **Pending** booking for `charlie` on "Electric Lawnmower" tomorrow from 12:00 PM - 1:00 PM. It verifies that a `ValidationError` is successfully thrown and logs `PASSED: Successfully blocked conflicting overlapping booking`.

* **Execution:**
  ```bash
  python manage.py seed_data --scenario overlap --clear
  ```

---

## Verifying in Django Admin

1. Run the development server:
   ```bash
   python manage.py runserver
   ```
2. Navigate to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) and log in using the seeded admin credentials:
   * **Username:** `admin_user`
   * **Password:** `admin123`
3. Click on **Bookings** or **Resources** to verify the created mock data and fields.
