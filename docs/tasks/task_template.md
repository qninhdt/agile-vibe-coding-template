# Task ID: [e.g., TASK-123] - [Concise Task Title - e.g., Create User Database Table]

## Description

<!-- a brief and concise description of the task -->

## Database Schema <!-- optional -->

<!-- data model diagram using dbml -->

<!-- if this task creates a new table -->

### `<data_model_name>`

```dbml
<data_model_definition>
```

- `<field_name>`: `<field_description>`

<!-- if this task doesnt create a new table -->

### `<data_model_name>` [#](../services/service_name.md#heading) <!-- link to existing data model -->

- Describe the modifications (optional)

## HTTP API Endpoints <!-- optional -->

### `<method> <endpoint>`

#### Description

<!-- a brief and concise description of the endpoint -->

#### Request

- **Parameters:** <!-- optional -->
    <!-- description of parameters should be included with json comment -->
  ```json
  {
    "field_name": "example_value" // short description if needed
  }
  ```
- **Query:** <!-- optional -->
    <!-- same as parameters -->
- **Body:** <!-- optional -->
    <!-- same as parameters -->

#### Response:

- `<status_code> <status_text>:` <status_description>
  - **Content-Type:** `<content_type>`
  - **Body:**
      <!-- description of body should be included with json comment -->
    ```json
    {
      "field_name": "example_value" // short description if needed
    }
    ```

## Design

<!--
- Provide a high-level, conceptual technical design and architecture.
- The document should be concise and brief.
- It is recommended to use other ways to describe the design instead of plain text if possible.
- Avoid redundant, unnecessary and trivial details and considerations.
- Use markdown bold for important points.
- Allow to use python-like pseudocode for algorithms in markdown code block (very complicated algorithms only)
- Avoid any reference to specific programming constructs (like methods, classes, functions, or particular syntax).
- Avoid any contents that are already covered in other documents like techstacks, coding guidelines, etc.
-->

### `<full_endpoint_name>`

#### Sequence Diagram <!-- optional -->

```mermaid
<sequence_diagram>
```

#### eg: Authentication, Rate Limit, etc. <!-- optional -->

## TODOs

<!-- list of features, methods, etc. that may appear in this task's source code when it is implemented but not covered in this task and could be implemented in future tasks, do not make it complicated so this section can be empty -->

- `TODO:` <description>

## References

<!-- link to related user stories, folders, modules, documentations -->

- <reference>
