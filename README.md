# Pysmith

> A set of Python tools focused on productivity

[![PyPI](https://img.shields.io/pypi/v/pysmith.svg)](https://pypi.org/project/pysmith/)
[![Python](https://img.shields.io/pypi/pyversions/pysmith.svg)](https://pypi.org/project/pysmith/)
[![License](https://img.shields.io/pypi/l/pysmith.svg)](https://github.com/isubero/pysmith/blob/main/LICENSE)

## ⚠️ Status: Work in Progress

Pysmith is under active development. Visit the github repository for updates.

## 🎯 Vision

Pysmith will be a modern set of python tools that combines:

- 🎨 **Elegance** - Clean, intuitive API design
- 🔧 **Craftsmanship** - Tools for artisan developers
- 📦 **Modularity** - Use only what you need

## 🚀 Roadmap

- [ ] Core classes and functions
- [ ] Pydantic adapters
- [ ] SQLAlchemy adapters
- [ ] Auth utilities
- [ ] CLI tooling
- [ ] Testing utilities
- [ ] Documentation

## 📦 Installation (Coming Soon)

```bash
pip install pysmith
```

## 💻 Quick Start (Planned)

```python
from pysmith.models import Model, Field

class User(Model):
    id: int = Field(autogenerate=True)
    name: str


user = User(name="John Doe")
user.save()

print(user.json())

#> {"id": "46657696-3477-43e8-996e-b71555fe3565", "name": "John Doe"}

```

## 🔨 CLI (Planned)

```bash
pysmith new myproject
pysmith forge model User
pysmith forge migration
pysmith db migrate
```

## 🤝 Contributing

Interested in contributing? Watch this repo for updates!

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🔗 Links

- **PyPI**: [pypi.org/project/pysmith](https://pypi.org/project/pysmith)
- **Repository**: [github.com/isubero/pysmith](https://github.com/isubero/pysmith)
- **Issues**: [github.com/isubero/pysmith/issues](https://github.com/isubero/pysmith/issues)

---

_Forging the future of Python web development_ ⚒️
