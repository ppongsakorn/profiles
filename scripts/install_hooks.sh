#!/bin/sh
# One-time per clone: use the repo's git hooks (PII guard on every commit).
git config core.hooksPath .githooks && chmod +x .githooks/pre-commit && echo "hooks enabled: .githooks/pre-commit"
