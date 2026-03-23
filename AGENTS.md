# Agent Operating Instructions & Domain Rulebook

Important: Before running the python command, first activate the venv if not activated. TO activate run from the root dir : venv\scripts\activate.

For frontend : Command npm run dev must be used in local.

## Part I: Core Agentic Reasoning Framework

Before taking any action (either tool calls or responses to the user), you must proactively, methodically, and independently plan and reason about:

1. **Logical Dependencies & Constraints:** Resolve conflicts strictly via policy rules > operational order > prerequisites > user constraints.
2. **Risk Assessment:** Evaluate future states before acting. Prioritize tool execution over user prompting for optional parameters unless logically required later.
3. **Abductive Reasoning:** Look beyond obvious causes. Formulate, test, and prioritize hypotheses based on likelihood without discarding low-probability edge cases prematurely.
4. **Outcome Evaluation:** Continuously adapt plans based on new observations and disproven hypotheses.
5. **Information Availability:** Exhaustively leverage tools, policies, context history, and the user before acting.
6. **Precision & Grounding:** Quote exact policies and reference specific state data to back up reasoning.
7. **Completeness:** Incorporate all requirements exhaustively. Do not assume inapplicability without verification.
8. **Persistence:** Intelligently retry on transient errors until a strict limit is hit; pivot strategy on structural errors.
9. **Response Inhibition:** Complete all planning steps 1-8 _before_ generating an action or response.

---

## Part II: Domain "Antigravity" Rulesets (Django/Postgres/DRF Stack)

Apply these specialized constraints and standards during Step 1 (Logical Dependencies & Constraints) of the Core Framework.

### 1. Cybersecurity Expert Rules

- **Zero Trust Architecture:** Never trust, always verify. APIs must use robust authentication (e.g., SimpleJWT for stateless tokens or DRF TokenAuthentication).
- **Principle of Least Privilege (PoLP):** Enforce strict DRF Permissions (`IsAuthenticated`, custom object-level permissions). Never leave endpoints with `AllowAny` unless explicitly required.
- **Django Security Settings:** Ensure `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE` are enforced in production. Use Django's built-in Argon2 or PBKDF2 password hashers.
- **Input Defense:** Rely on DRF Serializers for strict data validation to prevent injection. Never execute raw SQL queries (`.raw()`) without utilizing parameterized inputs.

### 2. System Designer Rules

- **Scalability First:** Deploy stateless Django applications using WSGI (Gunicorn/uWSGI) behind a reverse proxy (Nginx). Design for horizontal scale.
- **Asynchronous Decoupling:** Never block Django's synchronous request/response cycle with long-running tasks. Mandate **Celery** with Redis or RabbitMQ for background processing and email dispatch.
- **Caching Strategy:** Utilize `django-redis` for caching heavy database queries and slow DRF endpoints (e.g., `@method_decorator(cache_page)`). Ensure strict cache invalidation on model saves.
- **Observability:** Centralize logs using Python's `logging` module configured for JSON output. Implement tools like Sentry for error tracking and APM (Application Performance Monitoring).

### 3. Database Designer Rules (PostgreSQL Focus)

- **ACID & Constraint Enforcement:** Rely heavily on PostgreSQL. Use Database constraints (Unique, Check constraints) directly via Django models (`UniqueConstraint`, `CheckConstraint`) rather than just application-level validation.
- **ORM Optimization (Crucial):** Absolutely prohibit N+1 queries. Mandate the strict use of `select_related()` for foreign keys and `prefetch_related()` for many-to-many/reverse relations in all DRF ViewSets.
- **Postgres Specifics:** Leverage PostgreSQL-specific fields (`JSONField`, `ArrayField`, `TrigramExtension` for search) where they provide clear performance or structural advantages over standard relational tables.
- **Resilience & Indexing:** Require connection pooling using `PgBouncer` or Django 5.1+'s built-in connection pooler. Use `db_index=True` or `Index` classes for frequently filtered/ordered columns.

### 4. API Designer Rules (DRF Focus)

- **RESTful Purity & ViewSets:** Utilize DRF `ModelViewSet` and Routers for standard CRUD, keeping URLs resource-oriented (e.g., `/api/v1/users/`). Use `APIView` or `@api_action` for distinct behaviors.
- **Strict HTTP Semantics:** Map DRF actions correctly (GET for `list`/`retrieve`, POST for `create`, PUT/PATCH for `update`/`partial_update`, DELETE for `destroy`).
- **Standardized Responses:** Use DRF's `rest_framework.status` module explicitly (e.g., `status.HTTP_201_CREATED`) rather than hardcoded integers.
- **Forward Compatibility:** Implement URI versioning (e.g., `/api/v1/...`) and strictly enforce DRF pagination (`PageNumberPagination` or `CursorPagination`) globally for all list endpoints.

### 5. Django REST Framework Developer Rules

- **Fat Models, Skinny Views:** Keep DRF Views clean. Push core business logic into Django Models, custom Model Managers, or dedicated Service Layer classes.
- **Rigorous Serialization:** Use `ModelSerializer` for database mapping, but explicitly define `read_only_fields` to prevent mass-assignment vulnerabilities. Use `SerializerMethodField` cautiously as it cannot be optimized by the database.
- **Dependency & Setting Management:** Utilize `django-environ` or similar to keep all secrets, database credentials, and API keys completely out of the codebase.
- **Testing & Quality:** Mandate high test coverage using `pytest-django`. Use `APIClient` to write comprehensive integration tests for every endpoint, ensuring both successful flows and error handling (400, 401, 403, 404) are verified.
