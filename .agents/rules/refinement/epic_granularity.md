# Epic Granularity & Single Responsibility Principle Rule

## Single Responsibility Rule for Epics
Each classified epic MUST focus on a SINGLE responsibility, layer, or functional module.
Do NOT use conjunction words such as `and`, `with`, `plus`, or `&` in epic names or directory slugs (`epic_<number>_<name>`).

- ❌ Incorrect (Composite/Over-broad): `epic_1_domain_entities_and_contracts`
- ❌ Incorrect (Composite/Over-broad): `epic_4_di_wiring_and_main_server`
- ❌ Incorrect (Composite/Over-broad): `epic_5_docker_with_cloud_run`
- ⭕ Correct (Single Responsibility): `epic_1_domain_entities`
- ⭕ Correct (Single Responsibility): `epic_2_repository_contracts`
- ⭕ Correct (Single Responsibility): `epic_3_di_container_setup`
- ⭕ Correct (Single Responsibility): `epic_4_cmd_main_server`
- ⭕ Correct (Single Responsibility): `epic_5_dockerfile_containerization`
