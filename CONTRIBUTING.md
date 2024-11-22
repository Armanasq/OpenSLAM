# Contributing to OpenSLAM

Thank you for considering contributing to OpenSLAM! This open-source platform aims to democratize the SLAM community, enabling users to learn, test, develop, compare, and analyze SLAM techniques using KITTI-format data and other resources. We welcome contributions that improve, expand, and enrich this project.

Below are the guidelines to help you contribute effectively.

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [How to Contribute](#how-to-contribute)
3. [Code Guidelines](#code-guidelines)
4. [Pull Request Process](#pull-request-process)
5. [Issues and Feature Requests](#issues-and-feature-requests)
6. [Community and Support](#community-and-support)
7. [License](#license)

---

## Getting Started

1. **Fork the Repository**: Visit [OpenSLAM on GitHub](https://github.com/Armanasq/OpenSLAM/) and click the "Fork" button in the top-right corner.
2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/your-username/OpenSLAM.git
   cd OpenSLAM
   ```
3. **Set Upstream Repository**:
   ```bash
   git remote add upstream https://github.com/Armanasq/OpenSLAM.git
   ```

4. **Install Dependencies**:
   - Ensure you have Python and necessary libraries installed.
   - Set up a virtual environment:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```
   - For SLAM-specific tools, ensure dependencies like ROS, OpenCV, or PyTorch are installed as required by the module you’re working on.

---

## How to Contribute

### Contributions We’re Looking For:
- **New Features**: Develop innovative tools or algorithms for SLAM.
- **Bug Fixes**: Help fix issues and improve stability.
- **Documentation**: Improve or expand project documentation.
- **Testing**: Write unit tests to ensure robustness.
- **Examples**: Add tutorial notebooks or datasets for new users.
- **Performance Optimization**: Improve the efficiency of existing algorithms.

---

## Code Guidelines

1. **Coding Style**:
   - Use **PEP 8** for Python code.
   - Ensure clear, descriptive comments and docstrings.
   - Use meaningful variable and function names.

2. **Commit Messages**:
   - Write concise and descriptive commit messages.
   - Example:
     ```
     Fix: Corrected data preprocessing bug in KITTI loader
     Feat: Added ORB-SLAM2 compatibility
     Docs: Updated README with installation instructions
     ```

3. **Branching**:
   - Use branches for your work. For example:
     ```bash
     git checkout -b feature-add-visual-slam
     ```

4. **Testing**:
   - Write tests for any new functionality in the `/tests` directory.
   - Ensure all tests pass before submitting a pull request.

---

## Pull Request Process

1. **Sync with Upstream**:
   ```bash
   git fetch upstream
   git merge upstream/main
   ```

2. **Run Tests**:
   Before submitting your pull request, ensure all tests pass:
   ```bash
   pytest
   ```

3. **Submit the Pull Request**:
   - Push your branch to your fork:
     ```bash
     git push origin feature-add-visual-slam
     ```
   - Open a pull request on the [OpenSLAM repository](https://github.com/Armanasq/OpenSLAM/).
   - Provide a detailed description of your changes and link any related issues.

4. **Review Process**:
   - The pull request will be reviewed by the maintainers.
   - Make updates if requested and respond to any comments.

---

## Issues and Feature Requests

- Check existing [issues](https://github.com/Armanasq/OpenSLAM/issues) before creating a new one to avoid duplication.
- To report a bug or request a feature, open a GitHub issue with the following template:
  - **Title**: A brief description of the issue.
  - **Description**: Include steps to reproduce (for bugs) or a detailed explanation (for feature requests).
  - **Environment**: Specify OS, Python version, and relevant tools.

---

## Community and Support

Join our growing SLAM community! Whether you’re a beginner or an expert, your contributions are valuable. For discussions and questions, you can:
- Open a discussion on the [GitHub Discussions page](https://github.com/Armanasq/OpenSLAM/discussions).
- Contact the maintainer directly: [Arman Asgharpoor](mailto:arman@example.com).

---

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as OpenSLAM.

---

Thank you for contributing to OpenSLAM! Together, we can make SLAM accessible to everyone.

--- 
