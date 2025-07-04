# KNOWN_ISSUES

## Issues Needing Fixes

- [ ] CPU占用率优化，在面对大数据量时窗口会出现卡顿

- [ ] PySerial快速接收大量数据时，疑似有丢数据线现象

- [ ] 当前版本针对接收到的数据如果没有读取到`\n`，则不会第一时间输出到数据接收区

- [ ] ATCommand页面的保存按钮功能暂未实现

- [ ] 目前首页窗口组件过多，得考虑重构或者利用更多弹窗而不是下拉按钮

- [ ] 首页的数据接收缓冲区操作逻辑仍待优化，向上加载旧数据，下滑加载新数据

- [ ] 目前打包之后Windows安全中心会提示软件不安全，可能是因为使用了requests库，后续考虑转为PySide6内置网络请求库


## Issues Fixed

- [x] 新增EndWithOther参数至顶部Settings-MoreSettings菜单中，供用户自定义指令结尾符，输入的格式为Ascii码字符

- [x] 页面的`Ctrl+F`搜索框基本功能已实现，支持字符匹配和正则匹配

- [x] 添加软件层面的发送数据回显功能，可以直接显示使用工具发送出去的数据

- [x] 添加ATCRegex至顶部Settings-MoreSettings菜单中，供用户自定义指令匹配格式

- [x] 添加MaxRowOfButtonGroup至顶部Settings-MoreSettings菜单中，供用户自定义按钮组最大行数

- [x] 