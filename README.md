# My_fucked_100_people 插件

## 简介

一个有趣且略带调侃性质的QQ群插件。使用 `/ccb <QQ号码>` 命令可以“关爱”指定群友的“呼吸频率”并随机生成“避税”毫升数，看看有谁大调查之后偷税漏税最多。

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)
![Fuck u](https://img.shields.io/badge/Fuck-100People!-red.svg?style=for-the-badge)

**核心功能：**

*   **税务追踪（关爱群友）**：记录指定QQ号被C的次数。
*   **随机“避税”**：每次大调查都会随机生成一个“避税”毫升数。
*   **“CB之神”识别**：通过配置文件设置“OP列表”，当试图对列表中的QQ号有非分之想时，会触发特殊回复“哥们，这b开了”。

## 命令教程

### 基本命令

*   **`/ccb <QQ号码>`**
    *   **功能**：大调查指定QQ号的“出现频率”并生成“避税”量。
    *   **用法**：
        *   `/ccb 123456789`
        *   `/ccb123456789` (空格可选)
        *   `/ccb (空格*n) 123456789`(这tm是什么)
    *   **说明**：
        *   首次大调查：显示“这是 {QQ号} 的第一次，你成功拿下一血）共查出{随机数}ml避税。”
        *   再次大调查：显示“这是Ta的第 {次数} 次。共查出{随机数}ml避税，真的太逊了。”

*   **`/rank [tax|freq|help]`**
    *   **功能**：查询排行榜。
    *   **用法**：
        *   `/rank tax`
        *   `/rank freq`
        *   `/rank help`
    *   **说明**
        *   help查看插件功能

### “CB之神”功能

当大调查的QQ号在配置文件的 `op_list` 中时，插件会回复“哥们，这b开了”，并跳过Fuck。

## 配置说明

插件配置文件 `config.toml` 会根据代码中的 `config_schema` 自动生成。

### 配置项

在 `[plugin]` 节点下：

*   `enabled` (bool, 默认: `true`): 是否启用插件。
*   `op_list` (list of str, 默认: `[]`): “CB之神”QQ号列表。例如: `op_list = ["123456789", "987654321"]`

### 示例配置文件

```toml
# My_fucked_100_people - 自动生成的配置文件
# 群u群u，你看

# 插件启用配置
[plugin]
# 是否启用插件
enabled = true
# CB之神列表，输入QQ号，例如 ['123456789', '987654321']
op_list = ["123456789", "987654321"]
```

## 开发版本日志

### v1.3.3

*   被可乐制裁了
*   新增排行榜 `/rank [tax|freq]`
*   排行榜帮助 `/rank help`
*   顶风作案

### v1.3.2/1.3.2-fix

*   我吃了一个Apple
*   实现基础怀孕堕胎功能
*   我喝了一瓶可乐
*   实验性的排行榜
*   可乐不好喝
*   Apple不好吃
*   fix版本去除了Logger

### v1.2.2

*   实现基础频率追踪功能
*   实现随机"避税"毫升数生成
*   实现"CB之神"识别功能（通过 `op_list` 配置）
*   实现大调查QQ头像并发送功能
*   遵循 MaiBot 插件开发规范，使用 `config_schema` 定义配置，由系统自动生成 `config.toml`
*   暂时去除长度

### v1.2

*   被迫更新
*   我吃了一个橘子
*   草饲所有人

### v1.1 (初始版本)

*   初始版本，让你体验ccb的快乐