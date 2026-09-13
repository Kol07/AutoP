## Naming Conventions:
1. Database naming convention should adhere to standards like snake_case for tables & columns using full English words, avoiding reserved SQL words, and maintaining a single style for singular or plural table.
  - Primary & Foreign Keys: Use id for primary keys and [singular_table_name]_id for foreign keys (e.g., user_id).
  - All IDs should be in ULID format.
  - Timestamp fields should be created_at, updated_at, deleted_at

2. Frontend naming convention should adhere to the standard React naming:
  - Components | PascalCase
  - Hooks & Utils | camelCase
  - Folders & Assets | kebab-case

3. Backend naming convention:
  - Collections | Plural nouns | /api/v1/users
  - Individual Items | Plural + ID | /api/v1/users/:id
  - Sub-resources | Hierachical | /api/v1/users/:id/orders
  - Actions | Verb at the end | /api/v1/users/:id/forgot-password

4. Backend project file & folders:
  - Folders | kebab-case
  - Routes | camelCase + suffix | user_routes.py
  - Services | camelCase + suffix | user_services.py
  - Models | PascalCase + suffix | User_model.py

5. URL design rules:
  - Lower kebab-case for all URLs (e.g: /api/v1/password-reset). Never use camelCase or snake_case in URLs
  - Let HTTP methods do the work. Do not include verbs in the endpoint paths

6. Code Semantics:
  - Use standard camelCase for local variables, objects, instances, and functions.
    - Prefix asynchronous functions with verbs like fetch, create, update, delete, or calculate
  - Use PascalCase for Classes & Database Models
  
7. Request & Response payloads:
  - use camelCase for JSON payloads