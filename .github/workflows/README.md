# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for automated testing and code quality checks.

## Workflows

### `test.yml` - Continuous Integration

This workflow runs on every push and pull request to `main`, `session`, and `develop` branches.

#### Jobs

**1. Test** (Matrix: Ubuntu & macOS, Python 3.12)

- ✅ Run all 103 tests with pytest
- ✅ Type checking with mypy
- ✅ Linting with ruff

**2. Lint** (Code Quality)

- ✅ Format checking with ruff
- ✅ Code linting with ruff

**3. Coverage** (Test Coverage)

- ✅ Run tests with coverage tracking
- ✅ Upload coverage reports to Codecov (optional)

## Local Development

You can run the same checks locally before pushing:

```bash
# Run all tests
uv run pytest -v

# Type checking
uv run mypy src/pysmith/

# Linting
uv run ruff check src/ tests/ examples/

# Format checking
uv run ruff format --check src/ tests/ examples/

# Run tests with coverage
uv run pytest --cov=src/pysmith --cov-report=term-missing
```

## Status Badges

The README.md includes status badges that show:

- ✅ Tests passing/failing
- ✅ Code quality (ruff)
- ✅ Type checking (mypy)

## Configuration

### Dependencies

All required tools are defined in `pyproject.toml`:

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `mypy` - Type checking
- `ruff` - Linting and formatting

### Ruff Configuration

See `pyproject.toml` for ruff settings:

- Line length: 79 characters
- Per-file ignores for test files (F821 for forward references)

### Mypy Configuration

See `pyproject.toml` for mypy settings:

- Python version: 3.12
- Strict mode enabled
- Test files have relaxed checking

## Maintenance

### Adding New Checks

To add a new check to the CI pipeline:

1. Add the tool to `dependencies` in `pyproject.toml`
2. Add a new step in `.github/workflows/test.yml`
3. Test locally first with `uv run <command>`

### Updating Python Versions

Currently testing only Python 3.12 (project requirement: >= 3.12.3).

To add more Python versions:

```yaml
matrix:
  python-version: ["3.12", "3.13"]
```

## Troubleshooting

### Workflow Failing

1. Check the Actions tab on GitHub for detailed logs
2. Run the same commands locally to reproduce
3. Ensure all dependencies are installed with `uv sync --all-groups`

### Coverage Upload

The Codecov upload is optional and won't fail the build if the token is not set.

To enable:

1. Sign up at https://codecov.io
2. Add `CODECOV_TOKEN` to GitHub Secrets
3. Coverage reports will be automatically uploaded

## Next Steps

Potential improvements:

- [ ] Add deployment workflow for PyPI
- [ ] Add security scanning (e.g., bandit)
- [ ] Add dependency updates (e.g., Dependabot)
- [ ] Add performance benchmarks
- [ ] Add release automation
