# CI/CD Workflow Documentation

## 🚀 GitHub Actions CI/CD Pipeline

### Overview
This repository uses GitHub Actions for continuous integration and continuous deployment (CI/CD). The workflow automatically runs tests, security checks, and code quality analysis on every pull request and push to main branches.

### Workflow Structure

#### 📋 Jobs Overview
1. **build-and-test** - Core testing and coverage
2. **security-check** - Security vulnerability scanning  
3. **code-quality** - Code formatting and type checking
4. **build-summary** - Final status summary

### ⚡ Triggers

The CI/CD pipeline runs on:
- **Pull Requests** to `master`, `main` branches
- **Push** to `master`, `main`, `feature/add-unittest` branches

### 🛠️ Build Matrix

Tests run on multiple Python versions:
- Python 3.11
- Python 3.12

### 📦 Dependencies

#### Core Dependencies
- Flask 3.1.2
- Requests 2.32.5
- Firebase Admin 7.1.0
- Pillow 11.3.0
- And more (see `requirements.txt`)

#### Test Dependencies  
- pytest 8.4.2
- pytest-mock 3.15.1
- pytest-cov 7.0.0

### 🧪 Test Coverage

Current test coverage: **60%**

Breakdown by module:
- `api/login.py`: 100% coverage ✅
- `api/callback.py`: 97% coverage ✅
- `api/view.py`: 66% coverage ⚠️
- `api/app.py`: 0% coverage (not tested)
- `api/theme_dev.py`: 0% coverage (dev tool)

### 📊 Test Statistics

- **Total Tests**: 123
- **Test Files**: 4
  - `test_api_login.py`: 29 tests
  - `test_api_callback.py`: 25 tests  
  - `test_api_view.py`: 32 tests
  - `test_api_view_sg.py`: 37 tests

### 🔒 Security Checks

The pipeline includes security scanning with:
- **Safety**: Checks for known security vulnerabilities in dependencies
- **Bandit**: Static security analysis for common security issues

### 📝 Code Quality Checks

Automated code quality checks include:
- **Black**: Code formatting
- **isort**: Import sorting
- **MyPy**: Static type checking
- **Flake8**: Code linting

### 🏃‍♂️ Running Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=api --cov-report=html

# Run specific test file
pytest tests/test_api_view.py -v

# Run with maxfail (like CI)
pytest tests/ --maxfail=5 --disable-warnings -v
```

### 🛡️ Environment Variables for CI

The CI creates test environment variables:
```bash
SPOTIFY_CLIENT_ID=test_client_id
SPOTIFY_CLIENT_SECRET=test_client_secret  
REDIRECT_URI=http://localhost:5000/callback
```

### 📈 Coverage Reports

Coverage reports are generated in multiple formats:
- Terminal output (term-missing)
- HTML report (`htmlcov/index.html`)
- XML report (`coverage.xml`) for Codecov

### 🔧 Troubleshooting CI Issues

#### Common Issues:

1. **Test Failures**
   - Check test logs in GitHub Actions
   - Run tests locally to reproduce
   - Ensure all dependencies are installed

2. **Import Errors**
   - Verify Python path is correct
   - Check for missing dependencies
   - Ensure module structure is proper

3. **Coverage Drops**
   - Review coverage report
   - Add tests for uncovered code
   - Check for new untested modules

### 🎯 Future Improvements

- [ ] Increase test coverage to 80%+
- [ ] Add integration tests with real Spotify API
- [ ] Implement deployment automation
- [ ] Add performance testing
- [ ] Setup automated dependency updates

### 🤝 Contributing

When contributing:
1. Ensure all tests pass locally
2. Add tests for new features
3. Follow code quality standards
4. Check CI status before merging

### 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

*This CI/CD pipeline ensures code quality and reliability for the Spotify GitHub Profile project.* 🎵✨
