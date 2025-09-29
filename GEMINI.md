# Python 开发规范

本文档旨在为项目提供一套统一的Python代码风格、开发流程和最佳实践，以提高代码质量、可读性和可维护性。

## 1. 代码风格

本项目遵循 [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)。所有团队成员都应熟悉并遵守该规范。

### 1.1. 主要规则摘要

- **缩进**: 使用4个空格进行缩进，禁止使用Tab。
- **行长**: 每行代码最长不超过 88 个字符。
- **命名规范**:
    - `lowercase`: 变量、函数、模块。
    - `lower_case_with_underscores`: 变量、函数、模块。
    - `UPPER_CASE_WITH_UNDERSCORES`: 常量。
    - `CapitalizedWords` (CamelCase): 类名。
- **注释**:
    - 注释应简洁明了，解释“为什么”而不是“做什么”。
    - 复杂函数应包含文档字符串（docstrings），遵循 [PEP 257 -- Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)。
- **导入**:
    - 导入应始终位于文件顶部，仅在模块和常量声明之后。
    - 导入顺序：标准库 -> 第三方库 -> 本地应用/库。
    - 推荐使用绝对导入。

### 1.2. 自动化工具

为确保代码风格一致，项目集成以下工具：

- **Black**: 自动格式化代码，确保风格统一。
- **Ruff**: 一个极速的 Python Linter，用于检查代码中的错误和不规范的写法。

## 2. 开发环境

### 2.1. Python 版本

- 项目统一使用 `Python 3.10` 或更高版本。

### 2.2. 虚拟环境

- 所有开发都应在虚拟环境中进行，推荐使用 `venv`。
- 创建虚拟环境: `python -m venv venv`
- 激活虚拟环境:
    - Windows: `.\venv\Scripts\activate`
    - macOS/Linux: `source venv/bin/activate`

### 2.3. 依赖管理

- 项目依赖统一记录在 `requirements.txt` 文件中。
- 安装依赖: `pip install -r requirements.txt`
- 更新依赖:
    1. 手动修改 `requirements.txt`。
    2. 或使用 `pip freeze > requirements.txt` 导出当前环境的依赖。

## 3. Git 工作流

### 3.1. 分支模型

- `main`: 主分支，只包含稳定、可发布的版本。
- `develop`: 开发分支，包含最新的开发成果。
- `feature/<feature-name>`: 功能分支，用于开发新功能。
- `fix/<issue-name>`: 修复分支，用于修复 bug。

### 3.2. 提交信息

提交信息应遵循以下格式：

```
<type>: <subject>

[optional body]

[optional footer]
```

- **type**: `feat` (新功能), `fix` (修复), `docs` (文档), `style` (格式), `refactor` (重构), `test` (测试), `chore` (构建或辅助工具)。
- **subject**: 简洁描述本次提交的目的。

## 4. 测试

- 项目应包含单元测试，使用 `unittest` 或 `pytest` 框架。
- 测试代码应与源代码放在独立的 `tests/` 目录下。
- 运行测试: `pytest`

## 5. 文档

- 重要的业务逻辑和复杂的代码块必须有清晰的注释。
- 公共 API 和模块应有详细的文档字符串。
- 项目根目录下的 `README.md` 应包含项目简介、安装和使用指南。
