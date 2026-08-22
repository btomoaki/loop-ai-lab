# HTTP API & Web Interface Verification Harness Rule

## Rule Definition
1. **Dynamic Specification Mapping**: Endpoint URLs and ports MUST be mapped dynamically from `references/*.md` (e.g. `http://localhost:${PORT}<ENDPOINT_PATH>`).
2. **Real Curl Assertion**: Web API and Frontend epics MUST launch the server background process and use `curl` to assert HTTP status codes (`200 OK`, `201 Created`) and response headers.
3. **Template Standard**:
```bash
PORT="${PORT:-8080}"
TARGET_URL="http://localhost:${PORT}<TARGET_ENDPOINT_PATH_FROM_SPEC>"

<SERVER_LAUNCH_COMMAND> &
SERVER_PID=$!
sleep 2

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${TARGET_URL}")
kill "${SERVER_PID}" || true

if [ "${HTTP_STATUS}" -ne 200 ]; then
    echo "❌ API Verification Failed: HTTP Status ${HTTP_STATUS}"
    exit 2
fi
```
