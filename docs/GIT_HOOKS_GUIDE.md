# Git 钩子使用指南

本项目包含了两个重要的Git钩子来自动化开发流程：

## 🪝 可用的钩子

### 1. post-commit (提交后钩子)
**功能**: 自动递增版本号
- 每次提交后自动将 `.env` 文件中的版本号递增一个补丁版本
- 例如: `1.2.5` → `1.2.6`

### 2. commit-msg (提交信息钩子)  
**功能**: 验证提交信息格式
- 确保提交信息符合 [Conventional Commits](https://www.conventionalcommits.org/) 规范
- 格式: `<类型>(<范围>): <描述>`

## 🚀 安装和激活钩子

### 方法一：自动激活（推荐）
钩子文件已放置在 `.git/hooks/` 目录中，Git 会自动使用它们。

在Windows上，确保钩子有执行权限：
```bash
# 使用Git Bash
chmod +x .git/hooks/post-commit
chmod +x .git/hooks/commit-msg
```

### 方法二：手动验证钩子
```bash
# 测试版本更新器
python .git/hooks/test_version_updater.py

# 测试提交信息验证器
python .git/hooks/simple_test.py
```

## 📝 提交信息规范

### 支持的类型
| 类型 | 描述 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: add user authentication` |
| `fix` | 修复bug | `fix(api): resolve null pointer exception` |
| `docs` | 文档更新 | `docs(readme): update installation guide` |
| `style` | 代码格式化 | `style: format code with prettier` |
| `refactor` | 重构代码 | `refactor(auth): simplify login logic` |
| `test` | 测试相关 | `test: add unit tests for user service` |
| `chore` | 杂项任务 | `chore: update dependencies` |
| `perf` | 性能优化 | `perf: optimize database queries` |
| `ci` | 持续集成 | `ci: update GitHub Actions workflow` |
| `build` | 构建相关 | `build: configure webpack` |

### 格式规则

1. **基本格式**: `<类型>(<范围>): <描述>`
   - 类型: 必填，来自上表
   - 范围: 可选，用圆括号包围
   - 描述: 必填，至少5个字符

2. **示例**:
   ```
   feat: add user authentication system
   fix(api): resolve memory leak in user service  
   docs(readme): update installation instructions
   chore: bump version to 1.2.6
   ```

3. **破坏性变更**:
   ```
   feat!: redesign user authentication API
   fix(api)!: remove deprecated endpoint
   ```

### 特殊提交类型（自动跳过验证）
- `Merge` 提交
- `Revert` 提交  
- 自动版本更新提交（`chore: auto-increment version`）

## 🔧 版本自动递增

### 工作原理
1. 每次 `git commit` 后，post-commit 钩子会自动运行
2. 脚本读取 `.env` 文件中的当前版本号
3. 递增补丁版本号（例如：1.2.5 → 1.2.6）
4. 更新 `.env` 文件并自动提交更改

### 版本格式
遵循 [语义化版本](https://semver.org/) 规范：
- `主版本.次版本.补丁版本`
- 例如: `1.2.5`
- 每次提交后自动递增补丁版本

## 🛠️ 开发工作流示例

### 标准开发流程
```bash
# 1. 开发新功能
git add .
git commit -m "feat: add user login functionality"
# ✅ 提交信息验证通过
# 🔄 版本自动从 1.2.5 更新到 1.2.6

# 2. 修复bug
git add .
git commit -m "fix(auth): resolve token expiration issue"
# ✅ 提交信息验证通过  
# 🔄 版本自动从 1.2.6 更新到 1.2.7

# 3. 更新文档
git add .
git commit -m "docs: update API documentation"
# ✅ 提交信息验证通过
# 🔄 版本自动从 1.2.7 更新到 1.2.8
```

### 错误的提交消息示例
```bash
git commit -m "add login feature"
# ❌ 错误：提交信息格式不正确！
# 正确格式: feat: add login feature

git commit -m "fix: bug"  
# ❌ 错误：描述太短！至少需要5个字符
# 正确格式: fix: resolve authentication bug
```

## 🐛 故障排除

### 钩子没有运行
1. **检查钩子权限**:
   ```bash
   ls -la .git/hooks/
   # 确保 post-commit 和 commit-msg 有执行权限
   ```

2. **手动设置执行权限** (Linux/Mac):
   ```bash
   chmod +x .git/hooks/post-commit
   chmod +x .git/hooks/commit-msg
   ```

3. **Windows PowerShell** 用户：
   - Git 钩子应该自动工作
   - 确保安装了 Python 3.6+

### 提交信息验证失败
1. **查看错误信息**: 钩子会显示详细的错误和示例
2. **常见问题**:
   - 缺少类型前缀 (feat, fix 等)
   - 缺少冒号和空格 (`: `)
   - 描述太短 (少于5个字符)
   - 使用了无效的类型

### 版本更新问题
1. **检查 `.env` 文件格式**:
   ```
   VERSION='1.2.5'
   ```
2. **手动测试版本更新器**:
   ```bash
   python .git/hooks/test_version_updater.py
   ```

### 跳过钩子验证（紧急情况）
```bash
# 跳过所有钩子
git commit --no-verify -m "emergency fix"

# 或者临时重命名钩子
mv .git/hooks/commit-msg .git/hooks/commit-msg.bak
git commit -m "temporary commit"
mv .git/hooks/commit-msg.bak .git/hooks/commit-msg
```

## 📊 钩子管理

### 禁用钩子
```bash
# 临时禁用 commit-msg 钩子
mv .git/hooks/commit-msg .git/hooks/commit-msg.disabled

# 临时禁用 post-commit 钩子
mv .git/hooks/post-commit .git/hooks/post-commit.disabled
```

### 重新启用钩子
```bash
# 重新启用 commit-msg 钩子
mv .git/hooks/commit-msg.disabled .git/hooks/commit-msg

# 重新启用 post-commit 钩子  
mv .git/hooks/post-commit.disabled .git/hooks/post-commit
```

### 查看钩子状态
```bash
# 查看已安装的钩子
ls -la .git/hooks/ | grep -v sample

# 测试钩子功能
python .git/hooks/simple_test.py
```

## 💡 最佳实践

1. **提交前预览**: 使用 `git status` 和 `git diff` 检查更改
2. **描述清晰**: 提交信息要清楚描述做了什么
3. **小步提交**: 每个提交只做一件事
4. **遵循规范**: 始终使用规定的提交信息格式
5. **定期检查**: 偶尔查看版本号是否正确递增

## 🔗 相关资源

- [Conventional Commits](https://www.conventionalcommits.org/)
- [语义化版本](https://semver.org/)  
- [Git Hooks 文档](https://git-scm.com/book/zh/v2/%E8%87%AA%E5%AE%9A%E4%B9%89-Git-Git-%E9%92%A9%E5%AD%90)
