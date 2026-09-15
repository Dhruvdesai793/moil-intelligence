# Root Files

README.md provides startup, API and contribution instructions.
.gitignore excludes environments, secrets, caches, packaging output and generated raw/processed data.
backend/ owns FastAPI and adapter orchestration; frontend/ owns HTTP-only Streamlit.
data/ holds future input/materialized/sample files; notebooks/ holds signal-check experiments.
docs/ owns directory guidance and decisions.
No GitHub workflow, production infrastructure or real scientific artifact is configured.

Contribute through a scoped behavior change, tests, local end-to-end check and matching directory-guide update.
See HOW_THIS_PROJECT_WORKS.md for orchestration and BACKEND.md/FRONTEND.md for current endpoint linking.
