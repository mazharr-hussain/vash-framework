#!/bin/bash
# One AvA activity on a local Ollama model (used by .github/workflows/engine-local-model.yml).
# Passes when the loop runs end to end and writes an artifact and true logs; the verdict depends on the model.
set -euo pipefail
MODEL="$1"
WORK=$(mktemp -d)
export VASH_HOME="$PWD"
vash init "$WORK/demo"
cd "$WORK/demo"
python - "$MODEL" <<'PY'
import json, sys
model = sys.argv[1]
stack = json.load(open("project-stack.json"))
route = {"adapter": "ollama", "model": model, "timeout_s": 600}
stack["models"] = {
    "routes": {"local": {**route, "vendor": "local"}, "review": {**route, "vendor": "local-b"}},
    "intake": "local", "coder": "local", "critic": "review", "fallback": "local",
}
json.dump(stack, open("project-stack.json", "w"), indent=2)
PY
mkdir -p audit/prompts
printf 'type: code\n\nWrite a Python function add(a, b) that returns a + b. Reply with the code only.\n' \
  > audit/prompts/T-1_prompt.md
vash check --repo .
set +e
vash ava T-1 --repo .
code=$?
set -e
echo "vash ava exit code: $code (0 approved, 1 not approved; both are fine here)"
[ "$code" -le 1 ] || exit 1
test -s audit/artifacts/T-1_artifact.txt
log=audit/ava_logs/T-1_round1.md
test -s "$log"
grep -q "JUNIOR_ROUTE: local / $MODEL" "$log"
grep -q "Coder route unavailable" "$log" && { echo "The local model did not answer"; exit 1; }
echo "--- artifact"; cat audit/artifacts/T-1_artifact.txt
echo "--- round 1 log"; cat "$log"
