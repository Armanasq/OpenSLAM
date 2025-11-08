# Contributing to OpenSLAM

Thank you for your interest in contributing to OpenSLAM! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

---

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/OpenSLAM.git
   cd OpenSLAM/OpenSLAM_v0.1
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/OpenSLAM.git
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## 💻 Development Setup

### Backend Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run backend
python run_backend.py
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

---

## 🛠️ How to Contribute

### Types of Contributions

1. **Bug Fixes**: Fix issues reported in GitHub Issues
2. **New Features**: Implement new functionality
3. **Documentation**: Improve or add documentation
4. **Algorithm Plugins**: Add new SLAM algorithms
5. **Tests**: Add or improve test coverage
6. **Performance**: Optimize existing code

### Contribution Workflow

1. **Find or create an issue** describing what you want to work on
2. **Comment on the issue** to let others know you're working on it
3. **Develop your changes** following our coding standards
4. **Write tests** for your changes
5. **Update documentation** if needed
6. **Submit a pull request**

---

## 📝 Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **type hints** for function parameters and return values
- Write **docstrings** for all public functions and classes
- Maximum line length: **100 characters**
- Use **meaningful variable names**

Example:

```python
def process_frame(frame_data: Dict[str, Any], config: Dict) -> Dict[str, np.ndarray]:
    """
    Process a single frame from the dataset.

    Args:
        frame_data: Dictionary containing frame information
        config: Configuration parameters

    Returns:
        Dictionary with processed results including pose and features
    """
    # Implementation here
    pass
```

### JavaScript/React (Frontend)

- Follow **Airbnb JavaScript Style Guide**
- Use **functional components** with hooks
- Use **meaningful component and variable names**
- Add **PropTypes** or TypeScript types
- Maximum line length: **100 characters**

Example:

```javascript
const DatasetCard = ({ dataset, onSelect, isSelected }) => {
  const handleClick = () => {
    onSelect(dataset.id);
  };

  return (
    <div className={`dataset-card ${isSelected ? "selected" : ""}`}>
      <h3>{dataset.name}</h3>
      <button onClick={handleClick}>Select</button>
    </div>
  );
};
```

### File Organization

- Keep files focused on a single responsibility
- Group related functionality together
- Use clear, descriptive file names
- Maintain consistent directory structure

---

## 🧪 Testing Guidelines

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_dataset_manager.py

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage
```

### Writing Tests

- Write tests for all new features
- Aim for >80% code coverage
- Test edge cases and error conditions
- Use descriptive test names

Example:

```python
def test_dataset_validation_with_missing_calibration():
    """Test that validation fails when calibration file is missing."""
    manager = DatasetManager()
    is_valid, errors = manager.validate_kitti_format("/path/to/invalid/dataset")

    assert not is_valid
    assert "Missing required file: calib.txt" in errors
```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Update your branch** with the latest upstream changes:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests** and ensure they pass:

   ```bash
   pytest  # Backend
   npm test  # Frontend
   ```

3. **Check code style**:

   ```bash
   black backend/  # Python formatter
   npm run lint  # JavaScript linter
   ```

4. **Update documentation** if you changed APIs or added features

### Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated existing tests

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **At least one maintainer** must approve
3. **All comments** must be addressed
4. **Conflicts** must be resolved

---

## 🐛 Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Try the latest version** to see if it's already fixed
3. **Gather information** about your environment

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:

1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**

- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- Node.js version: [e.g., 18.0.0]
- Browser: [e.g., Chrome 120]

**Additional context**
Any other relevant information.
```

---

## 💡 Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Any other context, mockups, or examples.
```

---

## 🏗️ Adding Algorithm Plugins

### Plugin Structure

```
my_algorithm/
├── config.json           # Required: Algorithm metadata
├── launcher.py           # Required: Entry point
├── algorithm.py          # Implementation
├── README.md            # Documentation
├── requirements.txt     # Python dependencies
└── examples/            # Usage examples
```

### config.json Requirements

```json
{
  "name": "Algorithm Name",
  "category": "Visual SLAM | LiDAR SLAM | Visual-Inertial",
  "description": "Brief description",
  "author": "Your Name",
  "version": "1.0.0",
  "sensors": ["camera", "imu", "lidar"],
  "parameters": {
    "param1": "default_value"
  }
}
```

### Interface Implementation

Your algorithm must implement the `SLAMAlgorithm` interface:

```python
from shared.interfaces import SLAMAlgorithm

class MyAlgorithm(SLAMAlgorithm):
    def initialize(self, config: Dict) -> bool:
        """Initialize algorithm with configuration."""
        pass

    def process_frame(self, frame_data: Dict) -> Dict:
        """Process single frame."""
        pass

    def get_trajectory(self) -> np.ndarray:
        """Return full trajectory."""
        pass

    def get_map(self) -> Optional[Dict]:
        """Return map points."""
        pass
```

---

## 📚 Documentation

### Documentation Standards

- Use **Markdown** for all documentation
- Include **code examples** where appropriate
- Add **screenshots** for UI features
- Keep documentation **up-to-date** with code changes

### Where to Add Documentation

- **README.md**: Overview and quick start
- **API docs**: Docstrings in code
- **Wiki**: Detailed guides and tutorials
- **CHANGELOG.md**: Version history

---

## 🎯 Priority Areas

We especially welcome contributions in these areas:

1. **Testing**: Increase test coverage
2. **Documentation**: Improve and expand docs
3. **Performance**: Optimize slow operations
4. **Accessibility**: Improve UI accessibility
5. **Multi-dataset Support**: Add EuRoC, TUM formats
6. **Security**: Address security concerns

---

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: maintainer@openslam.org

---

## 🙏 Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

---

Thank you for contributing to OpenSLAM! 🚀
