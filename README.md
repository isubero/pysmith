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
# 1. Define your Model (for validation)
class User(Model):
    id: int
    username: str
    email: str
    age: Optional[int]

# 2. Validate incoming data
user_data = {"id": 1, "username": "alice", "email": "alice@example.com", "age": 30}
validated_user = User(**user_data)  # ✅ Pydantic validation

# 3. Convert to SQLAlchemy (for persistence)
UserSQLAlchemy = User.to_sqlalchemy_model(Base, table_name="users")

# 4. Save to database
with Session(engine) as session:
    db_user = UserSQLAlchemy(**user_data)
    session.add(db_user)
    session.commit()

# 5. Query and convert to DTO (for API response)
from pysmith.db import create_pydantic_model_from_sqlalchemy
UserDTO = create_pydantic_model_from_sqlalchemy(UserSQLAlchemy)
response = UserDTO(**db_user.__dict__)
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
