<div align="center">
  <h1>SCOM</h1>
  <p><i>一款适合你的开源串口通信工具</i></p>

  ![Platform](https://img.shields.io/badge/平台-Windows-orange)
  ![License](https://img.shields.io/badge/许可证-MIT-green)
  ![Language](https://img.shields.io/badge/语言-Python-yellow)

</div>
<p align="center">
  <a href="#一简介">简介</a> •
  <a href="#二系统要求">系统要求</a> •
  <a href="#三安装步骤">安装</a> •
  <a href="#五使用方法">使用方法</a> •
  <a href="#六自定义与扩展">自定义与扩展</a>
</p>

## 一、简介

![SCOM](./res/Samples.png)

**SCOM - Serial Communication**

是一个简单且易于扩展的开源串口通信工具，旨在为使用者提供便捷的方式与各种串口设备进行交互。

无论是开发人员还是测试人员，都可以在此项目的基础之上编写拓展自定义功能。

## 二、系统要求

- **操作系统**：Windows
- **Python 版本**：Python 3.6 及以上
- **依赖库**：
  1. PySide6：用于构建用户界面
  2. pyserial：实现串口通信功能

## 三、安装步骤

1. 确保您的系统满足上述系统要求
2. 如果尚未安装 Python，请从 [Python 官方网站](https://www.python.org/downloads/) 下载并安装适合您系统的版本
3. 安装依赖库：
   - 打开命令提示符或终端窗口
   - 运行以下命令安装 PySide6 和 pyserial：`pip install pyside6 pyserial`
4. 下载 SCOM：
   - 从 [SCOM](https://github.com/ifishin/SCOM) 下载最新版本的源代码或安装包
5. 如果是从源代码安装：
   - 解压下载的文件
   - 打开命令提示符或终端窗口，导航到解压后的目录
   - 运行以下命令进行安装：`python setup.py build`

## 四、目录结构及文件说明

以下是 SCOM 的目录结构：

```plaintext
SCOM/
│
├── components/
│   └── [compenents_modules_here]
├── config/
│   └── [config_files_here]
├── logs/
│   └── [tool_error_logs_here]
├── res/
│   └── [resource_files_here]
├── styles/
│   └── [style_files_here]
├── tmps/
│   └── [temporary_files_here]
├── utils/
│   └── [utility_modules_here]
├──.gitignore
├── README.md
├── Window.py
├── config.ini
├── favicon.ico
├── requirements.txt
├── run as admin.bat
├── setup.py
└── 一键运行.bat
```

- **components**：包含项目的组件模块，用于实现不同的功能。
- **config**：存放项目的配置文件，用于存储一些常用的设置。
- **logs**：存放工具的错误日志文件，方便后续分析和故障排查。
- **res**：包含项目的资源文件。
- **styles**：用于存储与界面样式相关的文件。
- **tmps**：临时文件目录，用于存储临时数据或在运行过程中生成的中间文件。
- **utils**：包含一些实用工具函数或模块。
- **Window.py**：主程序文件。
- **config.ini**：配置文件，存储一些常用的设置。
- **run as admin.bat**：Windows 下的批处理文件，用于以管理员权限运行程序，可以检查环境并安装所需的组件。
- **setup.py**：用于项目的安装和打包。
- **一键运行.bat**：用于在Windows下直接运行SCOM。

## 五、使用方法

1. 配置运行环境：

- 参考安装步骤，安装Python和依赖库：
在Windows环境中，也可以使用管理员权限执行`run as admin.bat`一键配置环境。

2. 启动 SCOM：

- 在命令提示符或终端窗口中，导航到 SCOM 的安装目录。
- 运行以下命令启动 SCOM：`python window.py`
在Windows环境中，也可使用`一键运行.bat`来启动SCOM

- 或者，如果您已经创建了可执行文件，可以直接运行该文件。
- 首次使用，可以直接以管理员权限点击运行目录下的`run as admin.bat`，一键配置好SCOM所需依赖

3. 操作手册

- 请查看[帮助文档](Help.md)了解SCOM的详细功能和操作方法。

## 六、自定义与扩展

1. **二次开发**：如果您是开发人员，可以对 SCOM 的源代码进行修改和扩展。您可以在 [SCOM](https://github.com/ifishin/SCOM)上fork源代码，并按照自己需求进行二次开发。
