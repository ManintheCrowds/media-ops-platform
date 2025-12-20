# Contributing Guidelines

Thank you for your interest in contributing to the Self-Hosted Platform Integration project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Documentation](#documentation)

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or insulting remarks
- Public or private harassment
- Publishing others' private information
- Other conduct that could reasonably be considered inappropriate

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.10 or 3.11 installed
- Docker and Docker Compose installed
- Git installed
- A GitHub account
- Basic knowledge of Python, FastAPI, and Docker

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/platform.git
   cd platform
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-org/platform.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

### 3. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your development settings
```

### 4. Start Development Services

```bash
# Start only required services (database)
docker-compose up -d postgres

# Or start all services
docker-compose up -d
```

### 5. Initialize Database

```bash
# Set DEBUG=True in .env
curl -X POST http://localhost:8000/api/auth/init-db
```

### 6. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Making Changes

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch (if used)
- **feature/***: New features
- **fix/***: Bug fixes
- **docs/***: Documentation updates
- **test/***: Test additions/improvements

### Creating a Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### Making Commits

1. **Stage your changes**:
   ```bash
   git add .
   # Or specific files
   git add path/to/file.py
   ```

2. **Commit with descriptive message**:
   ```bash
   git commit -m "feat: Add new service integration"
   ```

3. **Follow commit message conventions** (see [Development Guide](DEVELOPMENT.md#commit-messages))

### Keeping Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase your branch on upstream/main
git rebase upstream/main

# Or merge (if rebase conflicts)
git merge upstream/main
```

## Code Style

### Python Style

- Follow **PEP 8** style guide
- Use **Black** for code formatting (line length: 120)
- Use **type hints** for all functions
- Maximum line length: **120 characters**

### Formatting Code

```bash
# Format code with Black
black app services tests

# Check formatting
black --check app services tests
```

### Linting

```bash
# Run flake8
flake8 app services

# Run with configuration
flake8 app services --max-line-length=120
```

### Type Checking

```bash
# Run mypy
mypy app

# Or with configuration
mypy app --config-file=mypy.ini
```

### Code Style Checklist

Before submitting, ensure:

- [ ] Code follows PEP 8
- [ ] Code is formatted with Black
- [ ] No linting errors
- [ ] Type hints are used
- [ ] Docstrings are added
- [ ] No hardcoded secrets
- [ ] Error handling is implemented

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth_jwt.py

# Run with coverage
pytest --cov=app --cov=services --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Writing Tests

1. **Test Structure**: Follow existing test patterns
2. **Test Naming**: Use descriptive names
3. **Test Coverage**: Aim for 80%+ coverage
4. **Mock External Services**: Don't make real API calls in tests

### Test Checklist

- [ ] All tests pass
- [ ] New code has tests
- [ ] Tests are fast (< 1 second for unit tests)
- [ ] External services are mocked
- [ ] Edge cases are tested

## Pull Request Process

### Before Submitting

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**:
   ```bash
   pytest
   ```

3. **Format code**:
   ```bash
   black app services tests
   flake8 app services
   ```

4. **Update documentation** if needed

### Creating Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**:
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill out PR template

3. **PR Title**: Use conventional commit format
   ```
   feat: Add new service integration
   fix: Resolve authentication token expiration issue
   docs: Update API documentation
   ```

4. **PR Description**: Include
   - What changes were made
   - Why changes were made
   - How to test the changes
   - Screenshots (if UI changes)
   - Related issues

### PR Review Process

1. **Automated Checks**: CI/CD will run tests and linting
2. **Code Review**: Maintainers will review your code
3. **Address Feedback**: Update PR based on review comments
4. **Approval**: Once approved, PR will be merged

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests are added/updated
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] PR description is complete
- [ ] No merge conflicts
- [ ] Branch is up to date with main

## Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for solutions
3. **Verify it's a bug** (not a feature request)

### Creating an Issue

Use the appropriate issue template:

**Bug Report**:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages/logs

**Feature Request**:
- Clear description of the feature
- Use case/justification
- Proposed implementation (if applicable)
- Alternatives considered

**Example Bug Report**:
```markdown
## Description
Authentication fails when token expires.

## Steps to Reproduce
1. Login and get token
2. Wait 31 minutes
3. Make API request with token
4. Get 401 error

## Expected Behavior
Token should be refreshed automatically or provide clear error message.

## Actual Behavior
Returns 401 Unauthorized without explanation.

## Environment
- OS: Ubuntu 22.04
- Python: 3.10
- Platform version: 0.1.0
```

## Documentation

### When to Update Documentation

- Adding new features
- Changing API endpoints
- Modifying configuration
- Adding new services
- Fixing bugs that affect behavior

### Documentation Types

1. **Code Documentation**: Docstrings for functions/classes
2. **API Documentation**: Update API.md and OPENAPI.yaml
3. **Architecture Documentation**: Update ARCHITECTURE.md if needed
4. **User Documentation**: Update README.md and guides

### Writing Documentation

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep documentation up to date
- Cross-reference related sections

## Types of Contributions

### Code Contributions

- Bug fixes
- New features
- Performance improvements
- Refactoring
- Test improvements

### Documentation Contributions

- Fixing typos
- Improving clarity
- Adding examples
- Translating documentation
- Creating tutorials

### Other Contributions

- Reporting bugs
- Suggesting features
- Answering questions
- Reviewing PRs
- Improving CI/CD

## Getting Help

### Questions?

- Check existing documentation
- Search closed issues
- Ask in discussions (if available)
- Create a question issue

### Stuck?

- Review similar code in the codebase
- Check FastAPI/SQLAlchemy documentation
- Ask for help in PR comments

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md (if maintained)
- Credited in release notes
- Acknowledged in project documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Thank You!

Thank you for taking the time to contribute! Your efforts help make this project better for everyone.

## See Also

- [Development Guide](DEVELOPMENT.md) - Detailed development instructions
- [Architecture Documentation](ARCHITECTURE.md) - System architecture
- [API Documentation](API.md) - API reference
- [Service Integration Guide](SERVICE_INTEGRATION.md) - Adding new services


