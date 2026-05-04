# Contributing to CEMSS

First off, thank you for considering contributing to CEMSS! It's people like you that make CEMSS such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our commitment to fostering an open and welcoming environment. We pledge to make participation in our project a harassment-free experience for everyone.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots if relevant**
* **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior** and **explain the behavior you would like to see**
* **Explain why this enhancement would be useful**

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python style guide (PEP 8)
* Include thoughtful comments in your code
* Write meaningful commit messages
* Update documentation if needed
* Add tests if applicable

## Development Setup

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Pull AI models
ollama pull qwen2.5:0.5b
ollama pull moondream
```

### Running Tests

```bash
# Run full test suite
python test_full_system.py

# Run specific tests
python test_performance.py
python test_chatbot_general.py
```

### Code Style

* Follow PEP 8 for Python code
* Use meaningful variable and function names
* Add docstrings to functions and classes
* Keep functions focused and concise
* Comment complex logic

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

Example:

```
Add multi-camera simultaneous analysis

- Implement analyze_all_cameras endpoint
- Add permission checks for camera access
- Update chatbot service to handle multi-camera queries
- Add tests for new functionality

Fixes #123
```

## Project Structure

```
CEMSS/
├── api_chatbot.py          # Chatbot API endpoints
├── app.py                  # Main Flask application
├── config.py               # Configuration
├── models.py               # Database models
├── detection/              # Detection pipeline
│   ├── detection_pipeline.py
│   └── continuous_analyzer.py
├── utils/                  # Utilities
│   ├── chatbot_service.py
│   └── vlm_frame_analyzer.py
├── static/                 # Frontend assets
├── templates/              # HTML templates
└── tests/                  # Test files
```

## Areas for Contribution

### High Priority

- [ ] Mobile app development
* [ ] Docker/Kubernetes deployment
* [ ] Additional detection models
* [ ] Performance optimizations
* [ ] UI/UX improvements

### Medium Priority

- [ ] Multi-language support
* [ ] Cloud sync features
* [ ] Advanced analytics
* [ ] Custom model training tools
* [ ] REST API client libraries

### Good First Issues

- [ ] Documentation improvements
* [ ] Bug fixes
* [ ] Test coverage
* [ ] Code cleanup
* [ ] UI polish

## Recognition

Contributors will be:

* Listed in CONTRIBUTORS.md
* Mentioned in release notes
* Given credit in the README

## Questions?

Feel free to:

* Open an issue with the question label
* Reach out to maintainers
* Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to CEMSS!** 🎉
