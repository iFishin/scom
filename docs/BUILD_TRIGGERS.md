# 构建触发器使用指南

本项目支持在 `feature/modification` 分支上选择性触发构建工作流。

## 🚀 触发构建的方式

### 方式一：在 commit message 中使用关键词

在提交消息中包含以下任一关键词，将自动触发构建：

- `[build]` - 基础构建触发器
- `[release]` - 发布构建触发器
- `[package]` - 打包构建触发器
- `--build` - 替代语法
- `--release` - 替代语法
- `--package` - 替代语法

**示例：**
```bash
git commit -m "[build] feat: add new serial communication feature"
git commit -m "[release] chore: prepare v1.2.6 release"
git commit -m "fix: update documentation --build"
```

### 方式二：使用辅助脚本

#### Python 脚本 (推荐)
```bash
# 普通提交（不触发构建）
python scripts/build_helper.py "fix: update readme"

# 触发构建的提交
python scripts/build_helper.py -b "feat: add new feature"
python scripts/build_helper.py --release "chore: prepare release"
python scripts/build_helper.py --package "build: update dependencies"
```

#### Windows 批处理脚本
```cmd
# 普通提交（不触发构建）
scripts\commit.bat "fix: update readme"

# 触发构建的提交
scripts\commit.bat -b "feat: add new feature"
scripts\commit.bat --release "chore: prepare release"
scripts\commit.bat --package "build: update dependencies"
```

### 方式三：手动触发工作流

在 GitHub 仓库页面：
1. 进入 "Actions" 标签页
2. 选择 "scom_bundle" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并设置 `force_build` 为 `true`

## 📋 分支行为说明

| 分支 | 行为 |
|------|------|
| `main` | 🔨 **总是构建** - 每次推送都会触发构建 |
| `feature/modification` | 🎯 **选择性构建** - 只有包含触发关键词的提交才会构建 |
| 其他分支 | ⏭️ **不构建** - 不会触发构建工作流 |

## 🛠️ 工作流程示例

### 开发新功能（不需要立即构建）
```bash
git add .
git commit -m "feat: implement new feature"
git push
# ⏭️ 不会触发构建
```

### 完成功能开发（需要构建测试）
```bash
git add .
git commit -m "[build] feat: complete new feature implementation"
git push
# 🚀 会触发构建和发布
```

### 准备发布版本
```bash
git add .
git commit -m "[release] chore: prepare v1.2.6 release"
git push
# 🚀 会触发构建并创建预发布版本
```

## 🔧 高级用法

### 使用 Python 辅助脚本的交互模式
```bash
# 脚本会提示是否需要触发构建
python scripts/build_helper.py "fix: minor bug fixes"
```

### 跳过 pre-commit 钩子
```bash
python scripts/build_helper.py --no-verify -b "hotfix: critical bug fix"
```

### 查看当前分支和构建状态
```bash
python scripts/build_helper.py --help
```

## 📝 最佳实践

1. **开发阶段**：使用普通提交，避免不必要的构建
   ```bash
   git commit -m "wip: working on feature"
   ```

2. **功能完成**：添加构建触发器进行测试
   ```bash
   git commit -m "[build] feat: complete user authentication"
   ```

3. **发布准备**：使用release触发器
   ```bash
   git commit -m "[release] chore: bump version to 1.3.0"
   ```

4. **热修复**：使用build触发器快速构建
   ```bash
   git commit -m "[build] hotfix: critical security patch"
   ```

## 🐛 故障排除

### 构建未触发
- 检查分支名称是否为 `feature/modification`
- 确认 commit message 包含正确的触发关键词
- 查看 GitHub Actions 页面的工作流运行历史

### 构建意外触发
- 检查 commit message 是否意外包含了触发关键词
- 使用普通提交避免触发：`git commit -m "docs: update readme"`

### 工作流权限问题
- 确保仓库设置中启用了 GitHub Actions
- 检查 `GITHUB_TOKEN` 权限设置

## 📊 监控构建

- 访问 [GitHub Actions](https://github.com/iFishin/SCOM/actions) 查看构建状态
- 构建成功后会自动创建 GitHub Release
- Feature 分支的构建会标记为 "prerelease"
