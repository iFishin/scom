# 样式管理系统使用指南

## 📋 概述

现在您有了一套完整的样式批量管理解决方案，包含三个工具：

1. **font_manager.py** - 基础字体管理工具
2. **quick_style.py** - 快速样式管理工具  
3. **advanced_style_manager.py** - 高级样式管理工具

## 🔧 工具对比

| 功能 | font_manager | quick_style | advanced_style_manager |
|------|-------------|-------------|----------------------|
| 字体管理 | ✅ 基础 | ✅ 快速 | ✅ 完整 |
| 颜色管理 | ❌ | ✅ 基础 | ✅ 完整 |
| 主题预设 | ❌ | ✅ 内置 | ✅ 自定义 |
| 交互模式 | ❌ | ❌ | ✅ |
| 批量替换 | ❌ | ✅ | ✅ |
| 备份管理 | ✅ | ✅ | ✅ 完整 |

## 🚀 快速开始

### 日常使用 - quick_style.py

```bash
# 更改主要颜色（绿色 -> 蓝色）
python scripts/quick_style.py --primary-color '#007bff'

# 更改UI字体为苹方
python scripts/quick_style.py --ui-font '"PingFang SC", "Microsoft YaHei", sans-serif'

# 所有字体放大20%
python scripts/quick_style.py --scale-fonts 1.2

# 应用暗色主题
python scripts/quick_style.py --dark-theme

# 创建备份
python scripts/quick_style.py --backup
```

### 精确管理 - font_manager.py

```bash
# 查看当前字体设置
python scripts/font_manager.py --show

# 修改特定字体大小
python scripts/font_manager.py --size normal --value 15

# 全局字体缩放
python scripts/font_manager.py --scale 1.1
```

### 高级配置 - advanced_style_manager.py

```bash
# 显示完整配置
python scripts/advanced_style_manager.py --show

# 启动交互模式（推荐）
python scripts/advanced_style_manager.py --interactive

# 应用预设主题
python scripts/advanced_style_manager.py --theme blue_theme

# 批量正则替换
python scripts/advanced_style_manager.py --find 'padding: \d+px' --replace 'padding: 8px' --regex
```

## 🎨 主题预设

已预置的主题：
- **default** - 默认主题（绿色主题）
- **blue_theme** - 蓝色主题
- **large_text** - 大字体主题

### 使用主题

```bash
# 应用蓝色主题
python scripts/advanced_style_manager.py --theme blue_theme

# 应用大字体主题  
python scripts/advanced_style_manager.py --theme large_text
```

### 创建自定义主题

1. 启动交互模式：

```bash
python scripts/advanced_style_manager.py --interactive
```

2. 选择选项修改配置
3. 选择"保存为主题预设"
4. 输入主题名称

## 📁 文件结构

```
scripts/                     # 样式管理脚本目录
├── font_manager.py          # 基础字体管理工具
├── quick_style.py           # 快速样式管理工具
├── advanced_style_manager.py # 高级样式管理工具
├── unify_fonts.py           # 字体统一工具
└── fix_duplicate_comments.py # 修复重复注释工具

styles/
├── fish.qss                 # 主样式文件
├── style_config.json        # 样式配置文件
├── backups/                 # 自动备份目录
│   ├── fish_20250822_150001_manual.qss
│   └── fish_20250822_150203_font_change.qss
└── themes/                  # 主题预设目录
    ├── default.json
    ├── blue_theme.json
    └── large_text.json
```

## ⚠️ 重要注意事项

### QSS语法限制
- **QSS不支持变量定义**，只能在注释中做参考
- 所有"变量"都是通过批量替换实现的
- 修改前务必备份

### 备份策略
- 每次修改都会自动创建带时间戳的备份
- 手动备份：`python quick_style.py --backup`
- 备份位置：`styles/backups/`

### 安全使用
1. 修改前先备份
2. 测试修改效果
3. 如有问题，从备份恢复

## 🔄 常见操作

### 1. 更改整体配色

```bash
# 方式1：使用预设主题
python scripts/advanced_style_manager.py --theme blue_theme

# 方式2：修改主要颜色
python scripts/quick_style.py --primary-color '#e74c3c'

# 方式3：批量替换特定颜色
python scripts/quick_style.py --find '#00a86b' --replace '#9b59b6'
```

### 2. 调整字体系统

```bash
# 整体字体缩放
python scripts/quick_style.py --scale-fonts 1.15

# 修改特定字体族
python scripts/quick_style.py --ui-font '"Segoe UI", "Microsoft YaHei", sans-serif'

# 精确调整单个字体大小
python scripts/font_manager.py --size large --value 16
```

### 3. 主题切换

```bash
# 暗色主题
python scripts/quick_style.py --dark-theme

# 亮色主题
python scripts/quick_style.py --light-theme

# 自定义主题
python scripts/advanced_style_manager.py --theme your_custom_theme
```

### 4. 批量修改

```bash
# 修改所有圆角
python scripts/advanced_style_manager.py --find 'border-radius: \d+px' --replace 'border-radius: 12px' --regex

# 修改所有内边距
python scripts/advanced_style_manager.py --find 'padding: \d+px' --replace 'padding: 10px' --regex

# 修改特定颜色
python scripts/quick_style.py --find '#007bff' --replace '#28a745'
```

## 🆘 故障排除

### 样式不生效
1. 检查QSS语法是否正确
2. 重启应用程序
3. 检查是否有语法错误

### 恢复备份

```bash
# 查看备份文件
ls styles/backups/

# 手动恢复（替换fish.qss）
cp styles/backups/fish_20250822_150001_manual.qss styles/fish.qss
```

### 重置为默认

```bash
python scripts/advanced_style_manager.py --theme default
```

## 💡 最佳实践

1. **修改前备份**：`python scripts/quick_style.py --backup`
2. **小步迭代**：一次修改一个方面（字体/颜色/布局）
3. **使用主题**：为不同使用场景创建主题预设
4. **交互模式**：复杂修改使用交互模式
5. **测试验证**：修改后启动应用程序验证效果

## 📞 使用建议

- **日常使用**：推荐 `scripts/quick_style.py`
- **精确调整**：推荐 `scripts/font_manager.py`  
- **批量配置**：推荐 `scripts/advanced_style_manager.py --interactive`
- **主题管理**：推荐 `scripts/advanced_style_manager.py`
