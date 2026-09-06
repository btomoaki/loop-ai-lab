[INST]
=== 1. MANDATORY LANGUAGE & ARCHITECTURE RULES ===
{lang_rule_content}

{arch_rule_content}

=== 2. EXECUTION INSTRUCTIONS ===
{inst_content}

{existing_test_context}
[CRITICAL ARCHITECTURAL & CODING MANDATES]
1. The root module/package name in {project_file} and for all internal package imports MUST strictly be '{clean_mod_name}'.
2. NEVER prefix module names or internal imports with 'workspace/' or directory paths.
   - Correct:   import "{clean_mod_name}/internal/domain/model"
   - Forbidden: import "workspace/{clean_mod_name}/..." or "workspace/..."
3. [PACKAGE NAME COLLISION GUARD]: When importing both standard 'net/http' and internal '{clean_mod_name}/internal/interface/http',
   you MUST use an explicit alias for the internal package (e.g. `httpDelivery "{clean_mod_name}/internal/interface/http"`) to avoid 'redeclared' errors.
4. [STRICT PROHIBITION OF LOCKFILES]: NEVER generate or output 'go.sum', 'package-lock.json', or checksum files. Dependencies must be declared ONLY in {project_file}.
5. [NO UNAUTHORIZED SUBMODULES OR NESTED DIRECTORIES]: NEVER create 'go.mod' or 'go.sum' inside internal/ subdirectories.
6. [NO UNAUTHORIZED EXTERNAL LIBRARIES]: Do NOT import unapproved external libraries (e.g. gorilla/mux, time/rate) unless explicitly instructed in tasks.

=== 3. BACKLOG TASKS ===
{backlog_content}
{error_content}

[TASK: CEREMONY 3 STEPPED CODE GENERATION - {epic_name} (Sprint {sprint_num})]
Target Workspace Path: {target_ws_rel}
Project Root Module Name: {clean_mod_name}
Programming Language: {lang}
CURRENT TARGET LAYER FOCUS: {layer_name} ({layer_target})

[STRICT OUTPUT FORMAT MANDATE]
For EACH file, you MUST write '[FILE: relative/path/to/file]' on its own separate line immediately BEFORE its code block.
NEVER combine multiple files into a single code block. NEVER use '# FILE:' comments inside code blocks.
Example format:
[FILE: internal/domain/model/entity.go]
```{lang}
package model
...
```

Generate ONLY files belonging to the {layer_name} layer ({layer_target}).
[/INST]
