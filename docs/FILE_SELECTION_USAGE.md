# 文件选择功能使用指南

## 概述

Window.py 中的文件选择功能已进行参数化重构，使用统一的 `select_file()` 方法处理不同类型的文件选择场景。

## 核心方法

### `select_file(file_type="send")`

通用文件选择方法，支持多种文件类型的差异化处理。

**参数：**
- `file_type` (str): 文件选择的用途类型
  - `"send"` - 选择要发送的文件（默认）
  - `"log"` - 选择日志文件保存位置
  - `"json"` - 选择JSON配置文件
  - `"at_command"` - 导入AT命令文件

## 支持的文件类型配置

| 类型 | 模式 | 接受模式 | 文件过滤器 | 默认后缀 | 允许创建 |
|------|------|---------|----------|---------|---------|
| `send` | ExistingFile | AcceptOpen | txt, log, csv, bin, hex, dat, json | 无 | 否 |
| `log` | AnyFile | AcceptSave | txt, log, json | log | 是 |
| `json` | AnyFile | AcceptSave | json, txt | json | 是 |
| `at_command` | ExistingFile | AcceptOpen | json, txt, log | 无 | 否 |

## 使用示例

### 1. 选择要发送的文件
```python
# 调用默认的"send"类型（可以省略参数）
self.select_file()
# 或显式指定
self.select_file(file_type="send")
```

### 2. 选择日志文件保存位置
```python
self.select_file(file_type="log")
```

### 3. 选择或创建JSON配置文件
```python
# 如果需要传入特定的 QLineEdit 控件来接收路径
self.select_file(file_type="json")
# 或使用包装方法
self.select_json_file(path_input=self.some_line_edit)
```

### 4. 导入AT命令文件
```python
self.select_file(file_type="at_command")
# 或直接调用
self.import_at_command_file()
```

## 新增的回调方法

每种文件类型都有对应的回调方法处理选择完成后的逻辑：

- `_on_send_file_selected(file_path, allow_create)` - 处理发送文件选择
- `_on_log_file_selected(file_path, allow_create)` - 处理日志文件选择
- `_on_json_file_selected(file_path, allow_create)` - 处理JSON文件选择
- `_on_at_command_file_selected(file_path, allow_create)` - 处理AT命令文件选择

## 扩展新的文件类型

如需添加新的文件选择类型，只需在 `select_file()` 方法中的 `file_type_configs` 字典中添加新的配置：

```python
file_type_configs = {
    # ... 现有配置 ...
    "custom_type": {
        "mode": QFileDialog.ExistingFile,
        "accept_mode": QFileDialog.AcceptOpen,
        "filters": "Custom Files (*.custom);;All Files (*)",
        "title": "Select Custom File",
        "default_suffix": None,
        "allow_create": False,
        "callback": self._on_custom_file_selected  # 需要实现对应的回调方法
    }
}
```

然后实现对应的回调方法：

```python
def _on_custom_file_selected(self, file_path: str, allow_create: bool):
    """处理自定义文件选择完成的回调"""
    # 实现具体逻辑
    pass
```

## 优点

1. **集中管理** - 所有文件选择逻辑集中在一个方法中
2. **易于扩展** - 添加新的文件类型只需配置字典
3. **代码复用** - 避免重复的文件对话框创建代码
4. **一致的用户体验** - 所有文件选择操作使用统一的界面
5. **参数化** - 支持不同场景的差异化文件类型过滤

## 向后兼容性

现有的方法如 `select_json_file()` 和 `import_at_command_file()` 仍然可用，它们内部调用新的 `select_file()` 方法实现。
