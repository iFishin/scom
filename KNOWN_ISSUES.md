# KNOWN_ISSUES

## Issues Needing Fixes

- [ ] CPU占用率优化，在面对大数据量时窗口会出现卡顿
- [x] PySerial快速接收大量数据时，疑似有丢数据线现象
- [x] 当前版本针对接收到的数据如果没有读取到`\n`，则不会第一时间输出到数据接收区
- [ ] ATCommand页面的保存按钮功能暂未实现
- [ ] 目前首页窗口组件过多，得考虑重构或者利用更多弹窗而不是下拉按钮
- [x] 首页的数据接收缓冲区操作逻辑仍待优化，向上加载旧数据，下滑加载新数据
- [x] 目前打包之后Windows安全中心会提示软件不安全，可能是因为使用了requests库，后续考虑转为PySide6内置网络请求库
- [ ] 窗口更新触发逻辑得优化，现在的逻辑有点臃肿了
- [ ] Tool->String-Ascii(HEX)转化布局得优化，是否改成输入及时显示？再添加个选择转化类型
- [x] 串口数据以HEX显示的功能有问题，由于新增串口缓冲功能需要重新优化这部分
- [ ] 更新串口数据接收展示逻辑，DataReceiver只负责传递生数据，解析交由UI层处理
- [x] 结尾符在各个模块处得统一下，允许为空，允许自定义，但要给个默认值`\r\n`
- [ ] 


## Issues Fixed

- [x] 新增EndWithOther参数至顶部Settings-MoreSettings菜单中，供用户自定义指令结尾符，输入的格式为Ascii码字符

- [x] 页面的`Ctrl+F`搜索框基本功能已实现，支持字符匹配和正则匹配

- [x] 添加软件层面的发送数据回显功能，可以直接显示使用工具发送出去的数据

- [x] 添加ATCRegex至顶部Settings-MoreSettings菜单中，供用户自定义指令匹配格式

- [x] 添加MaxRowOfButtonGroup至顶部Settings-MoreSettings菜单中，供用户自定义按钮组最大行数

- [x] 