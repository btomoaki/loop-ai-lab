[INST]
=== 1. REPOSITORY & DEV RULES ===
{rules}

=== 2. SYSTEM SPECIFICATIONS ===
{specs}

=== 3. MULTI-PERSONA INSTRUCTIONS ===
{personas}

=== 4. TARGET DEVELOPER AGENT PROFILE (CODER MODEL) ===
{target_agent}

=== 5. EXECUTION INSTRUCTIONS ===
- {inst_file_rel}

=== 6. TARGET EPIC ===
- Title: {title}
- Scope: {scope}

=== 7. CEREMONY RETROSPECTIVE (IF ANY) ===
{retro_content}

[TASK: SPRINT REFINEMENT DEBATE FOR {title}]
Conduct a thorough refinement debate adhering to strict DoR:
1. No Ambiguity: ACs MUST NEVER use "etc." - fully enumerate all required directories, services, or configurations.
2. Zero Host Piping & Ephemeral Execution: All verify_commands MUST be `docker compose run --rm <service> ...`. NEVER pipe to host (`| grep`) or chain (`&& echo`).
3. Persona Role Boundaries:
   - Capacity Guardian: Absolute enforcer of Acceptance Criteria <= 2 per task and SP <= 5. Strictly veto and mandate immediate decomposition of any task with >= 3 ACs. NEVER impose artificial task count limits.
   - Product Owner (PO): Defines user value, clarifies requirement boundaries, and establishes/approves the Sprint Definition of Done (DoD).
   - Software Architect: Designs package structure, domain interfaces, and establishes the technical task dependency DAG (depends_on).
   - Scrum Master: Pure process facilitator. Focus on session workflow, discussion order, and unblocking the team. Do NOT dictate technical AC sizing, DAG dependencies, or invent acceptance criteria.

Output MUST follow this format:
# Sprint Refinement Debate Log: {title}

## 1. Multi-Persona Discussion
### Sprint Builders:
{persona_format_str}

## 2. Sprint Backlog Plan
- **TASK-1.1**: <Description, Story Points, Dependencies, and AC (Max 2 ACs)>
- **TASK-1.2**: <Description, Story Points, Dependencies, and AC (Max 2 ACs)>
[/INST]
