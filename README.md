# CodeArena Django Starter

A runnable Django starter for a Python practice and quiz platform. It includes student registration/login, separate student/admin dashboards, admin-managed MCQ quizzes, automatic quiz scoring, programming challenge publishing, and code submission storage for review.

## Important implementation notes
- This starter uses SQLite so it runs immediately and avoids the MongoDB Atlas HTTP 503 issue.
- Django does not natively support MongoDB through its standard ORM. If Atlas is mandatory, choose and configure a compatible integration or use a separate PyMongo data-access layer.
- Student challenge code runs in a browser Web Worker using Pyodide; the Django server stores submissions but does not execute them. Browser test results are for practice and are not authoritative for grading. Use a remote isolated sandbox before adding trusted server-side evaluation.
- Admins use `/admin-login/` and manage challenges, test cases, programs, and results in the app dashboard. Django Admin remains available to staff/superusers.

## Run locally

1. Install Python 3.10+.
2. Extract this folder and open a terminal in the folder containing `manage.py`.
3. Create and activate a virtual environment (recommended):

   Windows:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

   macOS/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Create database tables:
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   ```
6. Create the first admin account:
   ```bash
   python manage.py createsuperuser
   ```
   Alternatively, the first admin can use `/admin-signup/` from localhost while `DEBUG=True`. That one-time bootstrap is disabled as soon as an admin exists. To allow additional invite-only admin signups, set `DJANGO_ADMIN_SIGNUP_CODE` to a private, strong value before starting Django.

   Windows PowerShell:
   ```powershell
   $env:DJANGO_ADMIN_SIGNUP_CODE = "use-a-private-random-value"
   ```
7. Start the server:
   ```bash
   python manage.py runserver
   ```
8. Open `http://127.0.0.1:8000/`.
   - Student registration: `/register/`
   - Login: `/accounts/login/`
   - Admin login: `/admin-login/`
   - Admin signup: `/admin-signup/` (local one-time bootstrap or configured invitation code)
   - Student programs: `/programs/`
   - Admin dashboard: log in using your superuser account
   - Django Admin: `/admin/`

## Add a quiz
1. Log in to `/admin/` with your superuser.
2. Open **Quizzes**, add a title/topic/description and check **Published**.
3. Add questions in the inline section. Select the correct option and points for each question.
4. Save. The published quiz appears for students.

## Add a programming challenge
1. Sign in through `/admin-login/` and open **Manage challenges** from the admin dashboard.
2. Add the title, description, topic, difficulty, sample input/output, marks, and one or more input/expected-output test cases.
3. Check **Published** and save. Edit existing challenges and their test cases from the challenge manager.
4. Students open challenges under Programming Practice, run code in the browser IDE, then submit source code for instructor review.

## Manage programs and results
1. From the admin dashboard, choose **Create program** and add the event details, registration deadline and dates.
2. Publish the program to show it on the student Programs page. Drafts remain hidden.
3. Students register from `/programs/`; each student can register once per program.
4. From **Manage programs**, open **Manage results** for an event. Set each participant's status, score and feedback, then select **Publish result** to release it to that student.

## Security before deployment
- Replace the development `SECRET_KEY` using the `DJANGO_SECRET_KEY` environment variable.
- Set `DJANGO_DEBUG=False` and configure `DJANGO_ALLOWED_HOSTS`.
- Use HTTPS, secure cookies, rate limiting and backups.
- Add a sandboxed execution service before automatically running code.
