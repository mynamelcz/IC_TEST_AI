# test_gpio.py 说明文档

## 1. 概述

`test_gpio.py` 是 GPIO 外设的功能验证测试集，采用**纯 JTAG** 测试模式：通过两个 JTAG 探针（FT232H-A / FT232H-B）分别连接两颗相同的 MCU（MCU-A 与 MCU-B），利用寄存器读写完成所有 GPIO 功能的激励与采样，无需任何固件参与。

### 角色互换机制

每个测试用例均通过 `role` 参数进行两轮执行：

| 轮次 | 激励端 (stim) | 被测端 (dut) |
|------|--------------|-------------|
| 第 1 轮 | MCU-A | MCU-B |
| 第 2 轮 | MCU-B | MCU-A |

这样可确保两颗 MCU 的每个引脚都分别作为输出端和输入端被完整测试，排除单侧芯片缺陷的遗漏。

角色解析由内部函数 `_resolve(role, gpio_a, gpio_b, pin_pair)` 完成，返回激励端和被测端各自的 `GpioHelper` 实例、端口名、引脚号。

---

## 2. 依赖关系

### Fixture（定义于 `conftest.py`）

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `gpio_a` | session | MCU-A 的 `GpioHelper` 实例 |
| `gpio_b` | session | MCU-B 的 `GpioHelper` 实例 |
| `all_pin_pairs` | session | 从 `pin_map.yaml` 加载的全部引脚对列表 |

### 辅助函数

| 名称 | 来源 | 说明 |
|------|------|------|
| `reset_pin_pair(gpio_a, gpio_b, pin_pair)` | `conftest.py` | 将一对引脚的两侧同时复位为默认状态（输入模式、无上下拉、推挽、输出 0） |
| `_resolve(role, gpio_a, gpio_b, pin_pair)` | `test_gpio.py` 内部 | 根据 role 参数解析出激励端/被测端的 GPIO 实例与引脚信息 |
| `_pin_id(pin_pair, role)` | `test_gpio.py` 内部 | 生成可读的测试 ID 字符串，如 `MCU-B-PB5` |

### 辅助模块

| 模块 | 说明 |
|------|------|
| `GpioHelper`（`utils/gpio_helper.py`） | 封装 GPIO 寄存器操作的高层接口，提供 9 个方法和 7 个常量 |

`GpioHelper` 常量：

| 常量 | 值 | 含义 |
|------|----|------|
| `MODE_INPUT` | 0 | 输入模式 |
| `MODE_OUTPUT` | 1 | 输出模式 |
| `MODE_AF` | 2 | 复用功能模式 |
| `MODE_ANALOG` | 3 | 模拟模式 |
| `OTYPE_PUSH_PULL` | 0 | 推挽输出 |
| `OTYPE_OPEN_DRAIN` | 1 | 开漏输出 |
| `PULL_NONE` | 0 | 无上下拉 |
| `PULL_UP` | 1 | 上拉 |
| `PULL_DOWN` | 2 | 下拉 |

`GpioHelper` 方法：

| 方法 | 说明 |
|------|------|
| `set_mode(port, pin, mode)` | 设置引脚模式（MODER 寄存器） |
| `set_output_type(port, pin, otype)` | 设置输出类型（OTYPER 寄存器） |
| `set_pull(port, pin, pull)` | 设置上下拉（PUPDR 寄存器） |
| `write_pin(port, pin, value)` | 写输出电平（ODR 寄存器） |
| `read_pin(port, pin)` | 读输入电平（IDR 寄存器） |
| `reset_pin(port, pin)` | 复位引脚到默认状态 |
| `configure_exti(port, pin, rising, falling)` | 配置 EXTI 中断边沿 |
| `read_exti_pending(pin)` | 读取 EXTI 挂起标志 |
| `clear_exti_pending(pin)` | 清除 EXTI 挂起标志（写 1 清除） |

---

## 3. 引脚覆盖范围

引脚映射定义于 `config/pin_map.yaml`，共 **44 对**引脚：

| GPIO 端口 | 包含引脚 | 数量 | 排除引脚 |
|-----------|---------|------|---------|
| GPIOA | 0-12, 15 | 14 | PA13 (JTAG TMS)、PA14 (JTAG TCK) |
| GPIOB | 0-2, 5-15 | 14 | PB3 (JTAG TDO)、PB4 (JTAG TDI) |
| GPIOC | 0-15 | 16 | 无 |
| **合计** | | **44** | **4 个 JTAG 引脚** |

每对引脚的连接方式为：MCU-A 的某端口某引脚 与 MCU-B 的**同名**端口同号引脚一一对接。

---

## 4. 参数化策略

### role 参数

```python
ROLES = [
    ("MCU-A_stim", "MCU-B_dut"),
    ("MCU-B_stim", "MCU-A_dut"),
]
```

通过 `@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])` 装饰每个测试函数，生成两个参数化变体：

- `A_stim-B_dut`：MCU-A 作为激励端，MCU-B 作为被测端
- `B_stim-A_dut`：MCU-B 作为激励端，MCU-A 作为被测端

### 引脚遍历

每个测试函数内部通过 `for pp in all_pin_pairs` 遍历全部 44 对引脚。因此：

- 每个测试函数 = 2 个 role × 44 对引脚 = **88 次引脚级验证**
- 10 个测试函数合计 = **880 次引脚级验证**

---

## 5. 测试项清单（G-01 ~ G-10）

| 编号 | 函数名 | 测试内容 | 激励端动作 | 被测端动作 | 判定标准 |
|------|--------|---------|-----------|-----------|---------|
| G-01 | `test_output_high` | 输出高电平 | 设为输入、无上下拉 | 设为输出、写 1 | 激励端读到 1 |
| G-02 | `test_output_low` | 输出低电平 | 设为输入、无上下拉 | 设为输出、写 0 | 激励端读到 0 |
| G-03 | `test_input_read_high` | 输入读高 | 设为输出、写 1 | 设为输入、无上下拉 | 被测端读到 1 |
| G-04 | `test_input_read_low` | 输入读低 | 设为输出、写 0 | 设为输入、无上下拉 | 被测端读到 0 |
| G-05 | `test_pull_up` | 上拉电阻 | 设为输入、无上下拉（浮空） | 设为输入、使能上拉 | 被测端读到 1 |
| G-06 | `test_pull_down` | 下拉电阻 | 设为输入、无上下拉（浮空） | 设为输入、使能下拉 | 被测端读到 0 |
| G-07 | `test_open_drain` | 开漏输出 | 设为输入、使能上拉 | 设为开漏输出 | 写 0 时读到 0；写 1 时读到 1 |
| G-08 | `test_rising_edge_interrupt` | 上升沿中断 | 设为输出、先写 0 再写 1 | 设为输入、配置 EXTI 上升沿 | EXTI 挂起标志为 True |
| G-09 | `test_falling_edge_interrupt` | 下降沿中断 | 设为输出、先写 1 再写 0 | 设为输入、配置 EXTI 下降沿 | EXTI 挂起标志为 True |
| G-10 | `test_both_edge_interrupt` | 双沿中断 | 设为输出、0→1→0 | 设为输入、配置 EXTI 双沿 | 上升沿和下降沿挂起标志均为 True |

---

## 6. 各测试函数详细说明

### G-01: test_output_high — 输出高电平验证

**目的**：验证 DUT 的 GPIO 输出驱动能力，确认输出 HIGH 时对端能正确读取。

**步骤**：
1. `reset_pin_pair()` 复位引脚对到默认状态
2. 激励端：设为输入模式，无上下拉
3. 被测端：设为输出模式，写入高电平 (1)
4. 激励端：读取输入电平
5. 断言读取值 == 1

---

### G-02: test_output_low — 输出低电平验证

**目的**：验证 DUT 的 GPIO 输出低电平驱动能力。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输入模式，无上下拉
3. 被测端：设为输出模式，写入低电平 (0)
4. 激励端：读取输入电平
5. 断言读取值 == 0

---

### G-03: test_input_read_high — 输入读高电平验证

**目的**：验证 DUT 的 GPIO 输入采样能力，外部驱动 HIGH 时能正确读取。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输出模式，写入高电平 (1)
3. 被测端：设为输入模式，无上下拉
4. 被测端：读取输入电平
5. 断言读取值 == 1

---

### G-04: test_input_read_low — 输入读低电平验证

**目的**：验证 DUT 的 GPIO 输入采样能力，外部驱动 LOW 时能正确读取。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输出模式，写入低电平 (0)
3. 被测端：设为输入模式，无上下拉
4. 被测端：读取输入电平
5. 断言读取值 == 0

---

### G-05: test_pull_up — 上拉电阻验证

**目的**：验证 DUT 引脚内部上拉电阻功能，在外部浮空时能将电平拉高。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输入模式，无上下拉（浮空，不驱动线路）
3. 被测端：设为输入模式，使能上拉电阻
4. 被测端：读取输入电平
5. 断言读取值 == 1（上拉至高电平）

---

### G-06: test_pull_down — 下拉电阻验证

**目的**：验证 DUT 引脚内部下拉电阻功能，在外部浮空时能将电平拉低。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输入模式，无上下拉（浮空）
3. 被测端：设为输入模式，使能下拉电阻
4. 被测端：读取输入电平
5. 断言读取值 == 0（下拉至低电平）

---

### G-07: test_open_drain — 开漏输出验证

**目的**：验证 DUT 的开漏输出模式，写 0 时拉低线路，写 1 时释放线路（由外部上拉决定电平）。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输入模式，使能上拉电阻（提供外部上拉）
3. 被测端：设为输出模式，输出类型设为开漏
4. 被测端：写入 0 → 激励端读取，断言 == 0（开漏拉低）
5. 被测端：写入 1 → 激励端读取，断言 == 1（开漏释放，上拉拉高）

---

### G-08: test_rising_edge_interrupt — 上升沿中断验证

**目的**：验证 DUT 的 EXTI 上升沿中断检测功能。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输出模式，写入低电平 (0)
3. 被测端：设为输入模式，配置 EXTI 仅上升沿触发，清除挂起标志
4. 激励端：写入高电平 (1)，产生上升沿
5. 被测端：读取 EXTI 挂起标志
6. 断言挂起标志为 True

---

### G-09: test_falling_edge_interrupt — 下降沿中断验证

**目的**：验证 DUT 的 EXTI 下降沿中断检测功能。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输出模式，写入高电平 (1)
3. 被测端：设为输入模式，配置 EXTI 仅下降沿触发，清除挂起标志
4. 激励端：写入低电平 (0)，产生下降沿
5. 被测端：读取 EXTI 挂起标志
6. 断言挂起标志为 True

---

### G-10: test_both_edge_interrupt — 双沿中断验证

**目的**：验证 DUT 的 EXTI 同时配置上升沿和下降沿时，两种边沿均能触发中断。

**步骤**：
1. `reset_pin_pair()` 复位引脚对
2. 激励端：设为输出模式，写入低电平 (0)
3. 被测端：设为输入模式，配置 EXTI 双沿触发，清除挂起标志
4. 激励端：写入高电平 (1)，产生上升沿
5. 被测端：读取 EXTI 挂起标志（`pending_rise`），然后清除挂起标志
6. 激励端：写入低电平 (0)，产生下降沿
7. 被测端：读取 EXTI 挂起标志（`pending_fall`）
8. 断言 `pending_rise` 和 `pending_fall` 均为 True

---

## 7. CSV 报告集成

每个测试在每次引脚迭代中通过 `request.node.user_properties.append()` 记录以下字段：

| 字段 | 说明 | 示例值 |
|------|------|--------|
| `chip` | 被测 MCU 名称 | `MCU-B` |
| `pin` | 被测引脚标识 | `MCU-B-PB5` |
| `test_id` | 测试编号 | `G-01` |
| `test_name` | 测试名称 | `output_high` |
| `expected` | 期望值 | `1`、`low=0,high=1`、`True`、`rise=True,fall=True` |
| `actual` | 实际值 | 与 expected 格式对应 |

这些字段可通过自定义 pytest 插件或 `conftest.py` 中的 hook 导出为 CSV 报告，便于批量分析测试结果。

---

## 8. 运行命令

### Mock 模式（无需真实硬件）

```bash
pytest ic_test/tests/test_gpio.py --use-mock -v
```

### 生成 CSV 报告（需配合 CSV 报告插件）

```bash
pytest ic_test/tests/test_gpio.py --use-mock -v --csv=report.csv
```

### 指定真实 JTAG 探针

```bash
pytest ic_test/tests/test_gpio.py --jtag-a=FT232H-A --jtag-b=FT232H-B -v
```

### 仅运行特定测试

```bash
# 仅运行 G-01 输出高电平测试
pytest ic_test/tests/test_gpio.py::test_output_high -v --use-mock

# 仅运行 A_stim-B_dut 方向
pytest ic_test/tests/test_gpio.py -k "A_stim" -v --use-mock
```
