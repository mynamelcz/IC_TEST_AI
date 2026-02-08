# RISC-V MCU 数字功能自动化测试方案

**文档版本**：V1.0
**日期**：2026-02-09
**编写**：AI 辅助生成

---

## 目录

1. [概述](#1-概述)
2. [测试架构](#2-测试架构)
3. [软件分层设计](#3-软件分层设计)
4. [芯片接口抽象层](#4-芯片接口抽象层)
5. [GPIO 测试方案](#5-gpio-测试方案)
6. [UART 测试方案](#6-uart-测试方案)
7. [SPI 测试方案](#7-spi-测试方案)
8. [I2C 测试方案](#8-i2c-测试方案)
9. [Timer 测试方案](#9-timer-测试方案)
10. [ADC / DAC 测试方案](#10-adc--dac-测试方案)
11. [DMA 测试方案](#11-dma-测试方案)
12. [寄存器全覆盖测试](#12-寄存器全覆盖测试)
13. [时钟系统测试](#13-时钟系统测试)
14. [低功耗测试](#14-低功耗测试)
15. [压力测试](#15-压力测试)
16. [长时间稳定性测试](#16-长时间稳定性测试)
17. [异常处理策略](#17-异常处理策略)
18. [测试结果输出](#18-测试结果输出)
19. [实施步骤](#19-实施步骤)

---

## 1. 概述

### 1.1 测试对象

- **芯片类型**：RISC-V 内核 MCU
- **外设规格**：与 STM32H7 系列外设基本一致
- **测试阶段**：回片后芯片功能测试

### 1.2 测试目标

对 MCU 的数字外设进行全面的功能验证，覆盖以下外设：

- GPIO（全引脚覆盖）
- UART
- SPI
- I2C
- Timer / ADC / DAC / DMA（后续扩展）

### 1.3 测试硬件资源

| 资源 | 数量 | 用途 |
|------|------|------|
| FT232H | 2 个 | 通过 JTAG 接口控制 MCU |
| 被测 MCU | 2 颗 | 同款芯片，互为激励端和被测端 |
| pin-to-pin 对接板 | 2 块 | 将两颗 MCU 的外设引脚一一对接 |

### 1.4 测试软件环境

| 组件 | 说明 |
|------|------|
| 上位机语言 | Python |
| 测试框架 | pytest |
| MCU 固件语言 | C/C++ |
| JTAG 工具链 | FT232H MPSSE（具体工具可替换） |

---

## 2. 测试架构

### 2.1 系统拓扑

```
                    ┌──────────────────────────┐
                    │       PC (Python)        │
                    │  pytest + pyftdi + 报告   │
                    └─────┬──────────┬─────────┘
                          │ USB      │ USB
                    ┌─────┴───┐ ┌────┴────┐
                    │FT232H-A │ │FT232H-B │
                    │(JTAG-A) │ │(JTAG-B) │
                    └─────┬───┘ └────┬────┘
                     JTAG │          │ JTAG
                    ┌─────┴───┐ ┌────┴────┐
                    │  MCU-A  │ │  MCU-B  │
                    │ (激励端) │ │ (被测端) │
                    └────┬────┘ └────┬────┘
                         │ pin-to-pin│
                         ╚═══════════╝
                      SPI/I2C/UART/GPIO
```

### 2.2 核心思路

- **FT232H-A** 通过 JTAG 控制 **MCU-A**（激励端）
- **FT232H-B** 通过 JTAG 控制 **MCU-B**（被测端）
- **MCU-A ↔ MCU-B** 通过 pin-to-pin 对接板互联，做外设对拖测试
- PC 端 Python 协调两侧：发指令、收结果、判定 PASS/FAIL

### 2.3 角色互换机制

两颗芯片为同款 MCU，采用角色互换策略确保两颗芯片都被完整验证：

```
第一轮：MCU-A = 激励端，MCU-B = 被测端
第二轮：MCU-A = 被测端，MCU-B = 激励端
```

两轮使用同一份固件，PC 通过 JTAG 命令切换角色。

### 2.4 两种测试模式

| 模式 | 适用场景 | 工作方式 |
|------|---------|---------|
| 纯 JTAG 模式 | GPIO 等简单外设 | PC 通过 JTAG 直接读写寄存器，无需固件 |
| 固件模式 | UART/SPI/I2C 等通信外设 | PC 通过 JTAG 下载固件到 MCU，固件运行后执行收发，PC 通过 JTAG 读取结果 |

---

## 3. 软件分层设计

### 3.1 PC 端 Python 框架

```
ic_test/
├── conftest.py              # pytest 配置、fixture 定义
├── config/
│   ├── pin_map.yaml         # 引脚映射表（两颗芯片对接关系）
│   └── regs/
│       └── gpio.yaml        # GPIO 寄存器地址定义
├── drivers/
│   ├── chip_interface.py    # 芯片接口抽象层
│   └── jtag_impl.py         # JTAG 具体实现（可替换）
├── tests/
│   ├── test_gpio.py         # GPIO 测试用例
│   ├── test_uart.py         # UART 测试用例
│   ├── test_spi.py          # SPI 测试用例
│   ├── test_i2c.py          # I2C 测试用例
│   ├── test_timer.py        # Timer 测试用例
│   └── test_adc.py          # ADC 测试用例
└── utils/
    ├── report.py            # 测试报告生成（CSV + HTML）
    └── reg_parser.py        # Excel 寄存器表解析器
```

### 3.2 MCU 端 C 固件

```
firmware/
├── main.c                   # 主循环 + 测试入口
├── periph/
│   ├── uart_test.c/h        # UART 收发测试
│   ├── spi_test.c/h         # SPI 收发测试
│   ├── i2c_test.c/h         # I2C 收发测试
│   └── timer_test.c/h       # Timer 测试
├── hal/                     # 硬件抽象层（寄存器操作）
└── result/
    └── test_result.c/h      # 测试结果写入固定内存区域，供 PC 通过 JTAG 读取
```

**说明**：GPIO 测试使用纯 JTAG 模式，不需要固件。UART/SPI/I2C 等通信外设需要固件配合。

---

## 4. 芯片接口抽象层

测试代码通过统一的抽象接口操作芯片，屏蔽底层 JTAG 工具链的差异。更换工具链时只需替换实现类，测试逻辑无需修改。

### 4.1 接口定义

```python
class ChipInterface:
    """芯片操作抽象接口"""

    # 寄存器操作
    def reg_read(self, addr: int) -> int
    def reg_write(self, addr: int, value: int) -> None

    # 固件操作
    def download_firmware(self, path: str) -> None
    def run(self) -> None
    def halt(self) -> None
    def reset(self) -> None

    # 内存操作
    def mem_read(self, addr: int, size: int) -> bytes
    def mem_write(self, addr: int, data: bytes) -> None
```

### 4.2 使用方式

```python
# 测试代码中的使用示例
mcu_a = ChipInterface(jtag_id="FT232H-A")
mcu_b = ChipInterface(jtag_id="FT232H-B")

# 纯 JTAG 模式：直接操作寄存器
mcu_a.reg_write(GPIOA_MODER, 0x00000000)  # 设为输入
mcu_b.reg_write(GPIOA_MODER, 0x00000001)  # 设为输出
mcu_b.reg_write(GPIOA_ODR, 0x00000001)    # 输出 HIGH
val = mcu_a.reg_read(GPIOA_IDR)           # 读取输入

# 固件模式：下载固件并运行
mcu_a.download_firmware("uart_master.bin")
mcu_b.download_firmware("uart_slave.bin")
mcu_a.run()
mcu_b.run()
# ... 等待完成 ...
result = mcu_b.mem_read(RESULT_ADDR, RESULT_SIZE)
```

---

## 5. GPIO 测试方案

### 5.1 测试模式

采用**纯 JTAG 模式**，PC 直接通过 JTAG 读写 GPIO 寄存器，无需固件参与。

### 5.2 测试拓扑

```
  PC (Python pytest)
  ├── JTAG-A ──► MCU-A (激励端)
  └── JTAG-B ──► MCU-B (被测端)
                  │       │
                  └──GPIO──┘  pin-to-pin
```

- MCU-A 的 GPIO 引脚与 MCU-B 的 GPIO 引脚一一对接
- 全部 GPIO 引脚逐个测试，确保无坏针
- 第一轮：MCU-A 激励 / MCU-B 被测；第二轮：角色互换

### 5.3 GPIO 寄存器定义

| 寄存器 | 偏移 | 功能 |
|--------|------|------|
| MODER | 0x00 | 模式选择（00=输入, 01=输出, 10=复用, 11=模拟） |
| OTYPER | 0x04 | 输出类型（0=推挽, 1=开漏） |
| PUPDR | 0x0C | 上拉/下拉（00=无, 01=上拉, 10=下拉） |
| IDR | 0x10 | 输入数据寄存器（只读） |
| ODR | 0x14 | 输出数据寄存器 |

### 5.4 测试项清单

| 编号 | 测试项 | 激励端动作 | 被测端动作 | 判定标准 |
|------|--------|-----------|-----------|---------|
| G-01 | 输出高电平 | 设为输入，读取电平 | 设为输出 HIGH | 读到 HIGH = PASS |
| G-02 | 输出低电平 | 设为输入，读取电平 | 设为输出 LOW | 读到 LOW = PASS |
| G-03 | 输入读取高 | 输出 HIGH | 设为输入，读取并上报 | 上报 HIGH = PASS |
| G-04 | 输入读取低 | 输出 LOW | 设为输入，读取并上报 | 上报 LOW = PASS |
| G-05 | 上拉模式 | 设为高阻（浮空输入） | 设为上拉输入，读取 | 读到 HIGH = PASS |
| G-06 | 下拉模式 | 设为高阻（浮空输入） | 设为下拉输入，读取 | 读到 LOW = PASS |
| G-07 | 开漏输出 | 读取电平 | 设为开漏+外部上拉，输出0/1 | 电平匹配 = PASS |
| G-08 | 上升沿中断 | 输出 LOW→HIGH | 配置上升沿中断，上报是否触发 | 中断触发 = PASS |
| G-09 | 下降沿中断 | 输出 HIGH→LOW | 配置下降沿中断，上报是否触发 | 中断触发 = PASS |
| G-10 | 双沿中断 | 输出电平翻转 | 配置双沿中断，上报触发次数 | 每次翻转都触发 = PASS |

### 5.5 单引脚测试流程（以 G-01 输出高电平为例）

```
PC                         MCU-A(激励端)              MCU-B(被测端)
│                               │                         │
│─JTAG-A: 写MODER=输入模式──────►│                         │
│─JTAG-A: 写PUPDR=无上下拉──────►│                         │
│                               │                         │
│─JTAG-B: 写MODER=输出模式───────────────────────────────►│
│─JTAG-B: 写OTYPER=推挽──────────────────────────────────►│
│─JTAG-B: 写ODR=HIGH─────────────────────────────────────►│
│                               │                         │
│          等待稳定（数微秒）       │◄── pin-to-pin 电平 ──│
│                               │                         │
│─JTAG-A: 读IDR────────────────►│                         │
│◄─────── 返回 HIGH ────────────│                         │
│                               │                         │
│ 比对: 期望HIGH, 实际HIGH → PASS                          │
```

### 5.6 全引脚遍历逻辑

```python
# 伪代码
for pin in ALL_GPIO_PINS:
    for test_id, test_func in GPIO_TESTS:  # G-01 ~ G-10
        result = test_func(stimulator=mcu_a, dut=mcu_b, pin=pin)
        results.append(result)

# 角色互换，再测一轮
for pin in ALL_GPIO_PINS:
    for test_id, test_func in GPIO_TESTS:
        result = test_func(stimulator=mcu_b, dut=mcu_a, pin=pin)
        results.append(result)
```

- 每个引脚跑完 G-01 ~ G-10 全部测试项
- 两轮角色互换后，两颗芯片的每个引脚都被完整测试
- 每个测试项开始前，先将两端引脚复位为默认状态（输入浮空）

---

## 6. UART 测试方案

### 6.1 测试模式

采用**固件模式**。UART 收发时序由 MCU 内部波特率发生器驱动，无法纯靠 JTAG 操作寄存器实现。

PC 通过 JTAG 下载固件 → 启动运行 → 等待完成 → 读取结果内存区域。

### 6.2 测试拓扑

```
PC → JTAG-A → MCU-A (下载 UART 发送固件)
PC → JTAG-B → MCU-B (下载 UART 接收固件)
MCU-A TX ──pin-to-pin──► MCU-B RX
MCU-A RX ◄──pin-to-pin── MCU-B TX
```

### 6.3 测试项清单

| 编号 | 测试项 | 激励端动作 | 被测端动作 | 判定标准 |
|------|--------|-----------|-----------|---------|
| U-01 | 基本收发 | 发送已知数据 | 接收并存入内存 | 收发数据一致 = PASS |
| U-02 | 波特率遍历 | 逐个配置 9600/115200/921600/4.5M | 同步配置相同波特率 | 每个波特率收发正确 = PASS |
| U-03 | 数据位 | 配置 7/8/9 位数据 | 同步配置 | 数据正确 = PASS |
| U-04 | 停止位 | 配置 1/2 停止位 | 同步配置 | 数据正确 = PASS |
| U-05 | 校验位 | 配置 None/Odd/Even | 同步配置 | 数据正确 = PASS |
| U-06 | 大数据量 | 发送 1KB/10KB/64KB | 接收并校验 | 无丢失无错误 = PASS |
| U-07 | 流控 RTS/CTS | 启用硬件流控发送 | 启用硬件流控接收 | 流控信号正确 + 数据正确 = PASS |
| U-08 | 帧错误检测 | 故意发送错误帧 | 检查错误标志位 | 错误标志置位 = PASS |
| U-09 | 溢出检测 | 高速连续发送 | 不及时读取 | 溢出标志置位 = PASS |

---

## 7. SPI 测试方案

### 7.1 测试模式

采用**固件模式**。SPI 通信需要 Master 产生时钟，Slave 响应时钟，必须由固件驱动。

### 7.2 测试拓扑

```
PC → JTAG-A → MCU-A (SPI Master 固件)
PC → JTAG-B → MCU-B (SPI Slave 固件)
MCU-A MOSI ──pin-to-pin──► MCU-B MOSI
MCU-A MISO ◄──pin-to-pin── MCU-B MISO
MCU-A SCK  ──pin-to-pin──► MCU-B SCK
MCU-A CS   ──pin-to-pin──► MCU-B CS
```

角色互换：第一轮 A=Master / B=Slave，第二轮反过来。

### 7.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| S-01 | Mode 0 (CPOL=0,CPHA=0) | 全双工收发 | 双向数据一致 = PASS |
| S-02 | Mode 1 (CPOL=0,CPHA=1) | 全双工收发 | 双向数据一致 = PASS |
| S-03 | Mode 2 (CPOL=1,CPHA=0) | 全双工收发 | 双向数据一致 = PASS |
| S-04 | Mode 3 (CPOL=1,CPHA=1) | 全双工收发 | 双向数据一致 = PASS |
| S-05 | 时钟频率遍历 | 从低到高逐级测试 | 每个频率数据正确 = PASS |
| S-06 | 大数据量传输 | 1KB/10KB 连续传输 | 无丢失无错误 = PASS |
| S-07 | DMA 模式 | 使用 DMA 搬运 SPI 数据 | 数据正确 + DMA 完成标志 = PASS |
| S-08 | 片选行为 | 验证 CS 在传输前后的电平变化 | CS 时序正确 = PASS |

---

## 8. I2C 测试方案

### 8.1 测试模式

采用**固件模式**。I2C 通信需要 Master 产生时钟，Slave 响应，必须由固件驱动。

### 8.2 测试拓扑

```
PC → JTAG-A → MCU-A (I2C Master 固件)
PC → JTAG-B → MCU-B (I2C Slave 固件)
MCU-A SDA ◄──pin-to-pin──► MCU-B SDA  (开漏+上拉)
MCU-A SCL ◄──pin-to-pin──► MCU-B SCL  (开漏+上拉)
```

角色互换：第一轮 A=Master / B=Slave，第二轮反过来。

### 8.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| I-01 | 标准模式 100kHz | Master 读写 Slave | 数据一致 = PASS |
| I-02 | 快速模式 400kHz | Master 读写 Slave | 数据一致 = PASS |
| I-03 | 高速模式 1MHz+ | Master 读写 Slave | 数据一致 = PASS |
| I-04 | 7 位地址 | 使用 7 位从机地址通信 | 寻址成功 + 数据正确 = PASS |
| I-05 | 10 位地址 | 使用 10 位从机地址通信 | 寻址成功 + 数据正确 = PASS |
| I-06 | ACK/NACK | Master 访问不存在的地址 | 收到 NACK = PASS |
| I-07 | 多字节连续读写 | 连续读写 256 字节 | 数据一致 = PASS |
| I-08 | 时钟拉伸 | Slave 延迟响应 | Master 等待后正常完成 = PASS |
| I-09 | 总线错误恢复 | 模拟总线卡死后恢复 | 恢复后通信正常 = PASS |

---

## 9. Timer 测试方案

### 9.1 测试模式

采用**混合模式**：
- PWM 输出测试：固件模式（MCU-A 输出 PWM）+ 纯 JTAG 模式（MCU-B 用输入捕获或 GPIO 采样）
- 输入捕获测试：MCU-A 产生脉冲，MCU-B 捕获并记录

### 9.2 测试拓扑

```
PC → JTAG-A → MCU-A (Timer PWM 输出固件)
PC → JTAG-B → MCU-B (Timer 输入捕获固件)
MCU-A TIMx_CHx ──pin-to-pin──► MCU-B TIMx_CHx
```

角色互换：第一轮 A 输出 / B 捕获，第二轮反过来。

### 9.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| T-01 | PWM 输出频率 | 配置不同频率的 PWM 输出，对端捕获验证 | 频率误差 < 1% = PASS |
| T-02 | PWM 占空比 | 配置 10%/25%/50%/75%/90% 占空比 | 占空比误差 < 2% = PASS |
| T-03 | 输入捕获 | 一端输出已知频率脉冲，另一端捕获测量 | 捕获值与预期一致 = PASS |
| T-04 | 定时器计数 | 配置定时器自由运行，JTAG 读取计数值 | 计数值在递增 = PASS |
| T-05 | 定时器中断 | 配置溢出中断，验证中断触发 | 中断标志置位 = PASS |
| T-06 | 编码器模式 | 两路正交信号输入，验证计数方向和值 | 计数正确 = PASS |

---

## 10. ADC / DAC 测试方案

### 10.1 测试模式

采用**混合模式**：
- DAC 输出可通过 JTAG 直接写寄存器触发
- ADC 采样需要固件配合（配置通道、触发采样、读取结果）
- DAC→ADC 回环测试：同一颗芯片的 DAC 输出接到 ADC 输入，或跨芯片测试

### 10.2 测试拓扑

```
方式一：跨芯片测试
MCU-A DAC_OUT ──pin-to-pin──► MCU-B ADC_IN

方式二：同芯片回环（需板级跳线支持）
MCU-A DAC_OUT ──跳线──► MCU-A ADC_IN
```

### 10.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| AD-01 | DAC 输出精度 | DAC 输出多个电压值，ADC 采样验证 | 误差 < 1 LSB = PASS |
| AD-02 | ADC 线性度 | DAC 从 0 递增到满量程，ADC 逐点采样 | DNL/INL 在规格范围内 = PASS |
| AD-03 | ADC 多通道 | 逐个通道采样已知电压 | 每个通道数据正确 = PASS |
| AD-04 | ADC 采样率 | 配置不同采样率，验证数据完整性 | 无丢失 = PASS |
| AD-05 | ADC DMA 模式 | DMA 搬运 ADC 数据到内存 | 数据正确 + DMA 完成 = PASS |
| AD-06 | DAC 波形输出 | DAC + DMA 输出正弦波，ADC 采样验证 | 波形匹配 = PASS |

---

## 11. DMA 测试方案

### 11.1 测试模式

采用**固件模式**。DMA 传输需要 MCU 内核配置通道并启动，通过 JTAG 读取传输结果。

### 11.2 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| D-01 | 内存到内存 | DMA 搬运一块内存到另一块 | 目标数据与源一致 = PASS |
| D-02 | 外设到内存 | ADC/UART RX → 内存 | 数据正确 = PASS |
| D-03 | 内存到外设 | 内存 → UART TX / DAC | 对端接收正确 = PASS |
| D-04 | 循环模式 | DMA 循环搬运，验证多轮数据 | 每轮数据正确 = PASS |
| D-05 | 传输完成中断 | DMA 完成后触发中断 | 中断标志置位 = PASS |
| D-06 | 多通道优先级 | 多个 DMA 通道同时工作 | 所有通道数据正确 = PASS |

---

## 12. 寄存器全覆盖测试

### 12.1 测试模式

采用**纯 JTAG 模式**。PC 通过 JTAG 直接遍历所有外设寄存器，执行读写验证，无需固件。

### 12.2 数据来源

从现有的 Excel 寄存器表中解析以下信息：
- 寄存器名称、地址
- 各位域的名称、位范围
- 读写属性（RW / RO / WO / W1C 等）
- 复位默认值

### 12.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| R-01 | 复位值检查 | 芯片复位后读取所有寄存器 | 值与规格书默认值一致 = PASS |
| R-02 | 读写验证 | 对 RW 寄存器写入 0x55AA/0xAA55 后回读 | 回读值与写入值一致 = PASS |
| R-03 | 只读位验证 | 对 RO 位写入，验证值不变 | 写入后值未改变 = PASS |
| R-04 | 保留位验证 | 对保留位写入，验证行为符合规格 | 保留位保持默认值 = PASS |
| R-05 | W1C 位验证 | 写 1 清零类型位，验证清除行为 | 写 1 后该位变 0 = PASS |
| R-06 | 位域边界 | 写入每个位域的最大值和最小值 | 回读正确且不影响相邻位域 = PASS |

### 12.4 测试流程

```python
# 伪代码：从 Excel 寄存器表自动生成并执行测试
reg_table = parse_excel("register_map.xlsx")

for peripheral in reg_table.peripherals:
    for reg in peripheral.registers:
        # R-01: 复位值检查
        chip.reset()
        actual = chip.reg_read(reg.addr)
        assert actual == reg.reset_value

        # R-02: 读写验证（仅 RW 位）
        for pattern in [0x55555555, 0xAAAAAAAA]:
            write_val = pattern & reg.rw_mask
            chip.reg_write(reg.addr, write_val)
            read_val = chip.reg_read(reg.addr)
            assert (read_val & reg.rw_mask) == write_val

        # R-03: 只读位验证
        before = chip.reg_read(reg.addr)
        chip.reg_write(reg.addr, ~before & reg.ro_mask)
        after = chip.reg_read(reg.addr)
        assert (after & reg.ro_mask) == (before & reg.ro_mask)
```

---

## 13. 时钟系统测试

### 13.1 测试模式

采用**混合模式**：
- 时钟寄存器配置：纯 JTAG 模式
- 时钟输出验证：固件模式（MCU 将内部时钟输出到 MCO 引脚，对端 Timer 捕获测频）

### 13.2 测试拓扑

```
PC → JTAG-A → MCU-A (配置时钟 + MCO 输出)
PC → JTAG-B → MCU-B (Timer 输入捕获测频)
MCU-A MCO ──pin-to-pin──► MCU-B TIM_CH
```

### 13.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| C-01 | HSI 振荡器 | 使能 HSI，通过 MCO 输出测频 | 频率在规格范围内 = PASS |
| C-02 | HSE 振荡器 | 使能 HSE，通过 MCO 输出测频 | 频率与晶振标称值一致 = PASS |
| C-03 | LSI 振荡器 | 使能 LSI，验证 RTC 或 IWDG 可用 | 功能正常 = PASS |
| C-04 | PLL 配置 | 配置不同 PLL 倍频/分频参数 | MCO 输出频率与计算值一致 = PASS |
| C-05 | 系统时钟切换 | HSI→HSE→PLL 切换 | 切换后 MCO 频率正确 = PASS |
| C-06 | 外设时钟使能 | 逐个使能/禁用外设时钟 | 使能后寄存器可访问，禁用后不可访问 = PASS |
| C-07 | CSS 时钟安全 | 使能 CSS 后断开 HSE | 自动切换到 HSI + NMI 触发 = PASS |

---

## 14. 低功耗测试

### 14.1 测试模式

采用**固件模式**。MCU 需要执行 WFI/WFE 指令进入低功耗状态，必须由固件完成。
唤醒后通过 JTAG 读取状态寄存器和内存中的标志位来判定结果。

### 14.2 测试拓扑

```
PC → JTAG-A → MCU-A (唤醒源：GPIO 中断 / Timer / RTC)
PC → JTAG-B → MCU-B (下载低功耗固件，进入休眠)
MCU-A GPIO ──pin-to-pin──► MCU-B WKUP 引脚
```

- MCU-B 进入低功耗模式
- MCU-A 产生唤醒信号（GPIO 电平变化）
- PC 通过 JTAG-B 检测 MCU-B 是否成功唤醒

### 14.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| LP-01 | Sleep 模式进入 | 执行 WFI 进入 Sleep | CPU 停止，外设继续运行 = PASS |
| LP-02 | Sleep GPIO 唤醒 | 外部 GPIO 中断唤醒 | 唤醒后程序继续执行 = PASS |
| LP-03 | Sleep Timer 唤醒 | Timer 中断唤醒 | 唤醒后程序继续执行 = PASS |
| LP-04 | Stop 模式进入 | 进入 Stop 模式 | 大部分时钟停止 = PASS |
| LP-05 | Stop WKUP 唤醒 | WKUP 引脚唤醒 | 唤醒后时钟恢复 = PASS |
| LP-06 | Stop RTC 唤醒 | RTC 闹钟唤醒 | 唤醒后时钟恢复 = PASS |
| LP-07 | Standby 模式进入 | 进入 Standby 模式 | 仅备份域保持 = PASS |
| LP-08 | Standby WKUP 唤醒 | WKUP 引脚唤醒 | 芯片复位重启 = PASS |
| LP-09 | Standby RTC 唤醒 | RTC 闹钟唤醒 | 芯片复位重启 = PASS |
| LP-10 | 备份域数据保持 | Standby 前写入备份寄存器，唤醒后读取 | 数据保持不变 = PASS |

---

## 15. 压力测试

### 15.1 测试目标

验证 MCU 在多外设并发工作、高负载条件下的稳定性和正确性。芯片大厂（NXP、TI、Infineon 等）在回片测试中均包含此类测试，用于发现单外设测试无法暴露的总线竞争、DMA 冲突、中断嵌套等问题。

### 15.2 测试模式

采用**固件模式**。需要 MCU 同时运行多个外设，固件负责并发调度，PC 通过 JTAG 读取最终结果。

### 15.3 测试项清单

| 编号 | 测试项 | 说明 | 判定标准 |
|------|--------|------|---------|
| ST-01 | UART + SPI 并发 | UART 持续收发的同时，SPI 进行全双工通信 | 两路数据均正确 = PASS |
| ST-02 | UART + I2C 并发 | UART 持续收发的同时，I2C 进行读写 | 两路数据均正确 = PASS |
| ST-03 | SPI + I2C 并发 | SPI 全双工通信的同时，I2C 进行读写 | 两路数据均正确 = PASS |
| ST-04 | 三外设并发 | UART + SPI + I2C 同时工作 | 三路数据均正确 = PASS |
| ST-05 | 多通道 DMA 竞争 | 多个 DMA 通道同时搬运不同外设数据 | 所有通道数据正确，无覆盖 = PASS |
| ST-06 | 中断嵌套压力 | 多个外设同时产生中断，验证嵌套处理 | 所有中断均被正确响应 = PASS |
| ST-07 | 总线带宽压力 | DMA 高速搬运 + CPU 密集访问外设寄存器 | 无总线错误，数据正确 = PASS |
| ST-08 | GPIO + 通信外设并发 | GPIO 高频翻转的同时进行 UART/SPI 通信 | GPIO 波形正确 + 通信数据正确 = PASS |

### 15.4 测试流程

```
PC                         MCU-A(激励端)              MCU-B(被测端)
│                               │                         │
│─JTAG-B: 下载并发测试固件──────────────────────────────►│
│─JTAG-A: 下载并发激励固件─────►│                         │
│                               │                         │
│─JTAG-A: 启动运行─────────────►│                         │
│─JTAG-B: 启动运行──────────────────────────────────────►│
│                               │                         │
│                               │◄══ UART + SPI + I2C ══►│
│                               │   (多外设同时通信)        │
│                               │                         │
│          等待测试完成            │                         │
│                               │                         │
│─JTAG-B: 读取结果内存───────────────────────────────────►│
│◄─────── 各外设收发统计 ────────────────────────────────│
│                               │                         │
│ 逐项校验: UART数据 + SPI数据 + I2C数据 → 全部正确=PASS   │
```

### 15.5 关键验证点

- **总线仲裁**：AHB/APB 总线在多主设备同时访问时的仲裁是否正确
- **DMA 优先级**：不同优先级的 DMA 通道是否按预期调度
- **中断响应延迟**：高负载下中断响应是否在可接受范围内
- **数据完整性**：并发场景下各外设的数据是否互不干扰

---

## 16. 长时间稳定性测试

### 16.1 测试目标

验证 MCU 在长时间连续运行条件下的可靠性，发现间歇性故障（intermittent fault）和累积性问题。这是芯片大厂量产前必做的可靠性验证项目。

### 16.2 测试模式

采用**固件模式**。MCU 运行循环测试固件，PC 定期通过 JTAG 采集运行状态和错误计数。

### 16.3 测试项清单

| 编号 | 测试项 | 持续时间 | 说明 | 判定标准 |
|------|--------|---------|------|---------|
| LT-01 | UART 长时间收发 | ≥ 4 小时 | 持续收发数据，统计错误率 | 错误率 = 0 = PASS |
| LT-02 | SPI 长时间收发 | ≥ 4 小时 | 持续全双工通信 | 错误率 = 0 = PASS |
| LT-03 | I2C 长时间收发 | ≥ 4 小时 | 持续读写通信 | 错误率 = 0 = PASS |
| LT-04 | GPIO 长时间翻转 | ≥ 4 小时 | GPIO 持续高频翻转，对端采样验证 | 无错误翻转 = PASS |
| LT-05 | 多外设长时间并发 | ≥ 8 小时 | UART + SPI + I2C 同时持续运行 | 所有外设错误率 = 0 = PASS |
| LT-06 | 反复复位测试 | ≥ 1000 次 | 反复复位 MCU 并验证外设功能 | 每次复位后功能正常 = PASS |
| LT-07 | 低功耗循环 | ≥ 1000 次 | 反复进入/退出低功耗模式 | 每次唤醒后功能正常 = PASS |
| LT-08 | 时钟切换循环 | ≥ 1000 次 | 反复切换系统时钟源 | 每次切换后频率正确 = PASS |

### 16.4 监控与统计机制

```python
# 伪代码：长时间测试监控
test_start = time.time()
error_count = {"uart": 0, "spi": 0, "i2c": 0}
total_count = {"uart": 0, "spi": 0, "i2c": 0}

while time.time() - test_start < TEST_DURATION:
    # 定期通过 JTAG 读取 MCU 内存中的统计数据
    stats = mcu_b.mem_read(STATS_ADDR, STATS_SIZE)

    for periph in ["uart", "spi", "i2c"]:
        total_count[periph] = parse_total(stats, periph)
        error_count[periph] = parse_errors(stats, periph)

    # 实时输出进度
    elapsed = time.time() - test_start
    print(f"[{elapsed:.0f}s] UART: {total_count['uart']} pkts, "
          f"{error_count['uart']} errs | "
          f"SPI: {total_count['spi']} pkts, "
          f"{error_count['spi']} errs | "
          f"I2C: {total_count['i2c']} pkts, "
          f"{error_count['i2c']} errs")

    # 如果错误率超过阈值，提前终止
    for periph in ["uart", "spi", "i2c"]:
        if error_count[periph] > ERROR_THRESHOLD:
            report_failure(periph, error_count[periph])
            break

    time.sleep(POLL_INTERVAL)  # 每隔 N 秒采集一次
```

### 16.5 测试报告扩展

长时间稳定性测试的报告在标准 CSV/HTML 基础上增加：

- **运行时长**：实际测试持续时间
- **总传输量**：各外设累计收发数据量
- **错误统计**：各外设错误次数及错误率
- **错误时间分布**：错误发生的时间点（用于分析是否存在规律性故障）
- **温度记录**（如有温度传感器）：运行过程中芯片温度变化曲线

---

## 17. 异常处理策略

### 17.1 测试结果状态定义

| 状态 | 含义 | 说明 |
|------|------|------|
| PASS | 测试通过 | 实际结果与期望一致 |
| FAIL | 功能不正确 | 芯片问题，需要分析 |
| ERROR | 测试环境异常 | JTAG 断开、接线问题等，需排查环境 |

### 17.2 异常场景与处理方式

| 异常场景 | 处理方式 |
|---------|---------|
| JTAG 通信超时 | 重试 3 次，仍失败则标记 ERROR |
| 引脚冲突（两端同时输出） | 测试流程严格保证：先配置读取端为输入，再配置输出端 |
| 电平不稳定 | 读取后延时再读一次，两次一致才判定 |
| 复位残留 | 每个测试项开始前，先将两端引脚复位为默认状态（输入浮空） |
| 固件运行超时 | 设置看门狗超时，超时后 halt MCU 并标记 ERROR |
| 数据校验失败 | 记录期望值和实际值，标记 FAIL |

---

## 18. 测试结果输出

### 18.1 终端实时输出

采用 pytest -v 风格，实时显示每条用例的执行结果：

```
tests/test_gpio.py::test_output_high[MCU-A][PA0]  PASSED
tests/test_gpio.py::test_output_high[MCU-A][PA1]  PASSED
tests/test_gpio.py::test_output_high[MCU-A][PA2]  FAILED
tests/test_gpio.py::test_output_low[MCU-A][PA0]   PASSED
...
======================== 318 passed, 2 failed in 45.23s ========================
```

### 18.2 CSV 报告

自动生成 CSV 文件，方便归档和数据分析：

```csv
芯片,引脚,测试编号,测试项,期望值,实际值,结果,时间戳
MCU-A,PA0,G-01,输出高电平,HIGH,HIGH,PASS,2026-02-09 10:23:01
MCU-A,PA0,G-02,输出低电平,LOW,LOW,PASS,2026-02-09 10:23:01
MCU-A,PA2,G-01,输出高电平,HIGH,LOW,FAIL,2026-02-09 10:23:03
MCU-B,PA0,G-01,输出高电平,HIGH,HIGH,PASS,2026-02-09 10:25:12
...
```

### 18.3 HTML 报告

使用 pytest-html 插件自动生成 HTML 报告：

- 测试概览：总数 / 通过 / 失败 / 错误 / 通过率
- 失败详情：每条失败用例展开显示引脚、期望值、实际值、错误信息
- 支持按芯片、引脚、测试项筛选

生成命令：

```bash
pytest tests/ -v --html=report.html --self-contained-html
```

---

## 19. 实施步骤

### 第一步：基础框架搭建

1. 搭建 Python 项目结构（ic_test 目录）
2. 实现 ChipInterface 抽象层
3. 实现 JTAG 具体驱动（对接现有工具链）
4. 验证 PC ↔ MCU 的 JTAG 寄存器读写链路

### 第二步：GPIO 测试（先跑通端到端流程）

1. 实现 Excel 寄存器表解析器
2. 实现引脚映射配置加载
3. 编写 GPIO 测试用例（G-01 ~ G-10）
4. 验证全引脚遍历 + 角色互换
5. 验证 CSV + HTML 报告输出

### 第三步：UART 测试

1. 编写 MCU 端 UART 收发测试固件
2. 实现 PC 端固件下载 + 运行 + 结果读取流程
3. 编写 UART 测试用例（U-01 ~ U-09）

### 第四步：SPI / I2C 测试

1. 编写 MCU 端 SPI Master/Slave 测试固件
2. 编写 MCU 端 I2C Master/Slave 测试固件
3. 编写 SPI 测试用例（S-01 ~ S-08）
4. 编写 I2C 测试用例（I-01 ~ I-09）

### 第五步：Timer / ADC / DAC / DMA 测试

1. 编写 MCU 端 Timer PWM 输出 + 输入捕获固件
2. 编写 ADC/DAC 回环测试固件
3. 编写 DMA 传输测试固件
4. 编写测试用例（T-01~T-06, AD-01~AD-06, D-01~D-06）

### 第六步：寄存器全覆盖测试

1. 实现 Excel 寄存器表解析器（提取地址、位域、读写属性、复位值）
2. 自动生成寄存器读写测试用例（R-01~R-06）
3. 遍历所有外设寄存器执行验证

### 第七步：时钟系统 + 低功耗测试

1. 编写时钟配置 + MCO 输出固件
2. 编写低功耗进入/唤醒固件
3. 编写测试用例（C-01~C-07, LP-01~LP-10）

### 第八步：压力测试

1. 编写多外设并发测试固件（UART + SPI + I2C 同时运行）
2. 编写多通道 DMA 竞争测试固件
3. 编写中断嵌套压力测试固件
4. 编写测试用例（ST-01~ST-08）

### 第九步：长时间稳定性测试

1. 编写各外设循环收发测试固件（支持长时间运行 + 错误计数）
2. 实现 PC 端定期采集监控机制
3. 编写反复复位 / 低功耗循环 / 时钟切换循环测试固件
4. 编写测试用例（LT-01~LT-08）
5. 完善测试报告和统计功能

---

*文档结束*
