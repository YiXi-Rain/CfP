# CfP / CwU — 带单位的物理计算

当前维护版本：**CwU 0.261016**。项目保留 CfP 仓库名，以 `CwU.py` 为单文件入口。

需要 Python 3.10 或更新版本，无第三方依赖。将 `CwU.py` 放在计算脚本旁边即可使用，
也可以克隆仓库后直接在仓库目录编写脚本。

## 快速开始

```python
from CwU import Q, c, me

distance = Q(120, "cm", significance=3)
time = Q(2, "s", significance=2)
speed = distance / time

speed.show("m/s")                   # 0.60 m/s
print(speed.get_value("cm/s"))      # 60.0（原始浮点值，不按显示精度截断）
print((2 * distance).get_str("m"))  # 2.40 m
(me * c**2).show("MeV")             # 0.51099889 MeV
```

`Q` 是 `Quantity` 的简称，`from CwU import Quantity` 仍可使用。
乘除、乘方、加减和比较会处理单位；加减及大小比较要求量纲相容。
普通数字在乘除时视为精确系数，不减少有效数字位数。

## 数值、文本与打印

| 用法 | 返回结果 |
| --- | --- |
| `q.value` / `q.get_value()` | 当前对象单位制下的原始数值 |
| `q.get_value("cm")` | 指定单位下的浮点数值，检查量纲 |
| `str(q)` / `q.get_str()` | 当前单位表示的字符串 |
| `q.get_str("cm")` | 指定单位下的字符串，遵守显示设置 |
| `q.show("cm")` | 打印并返回原对象 |
| `q.unit_dict` | 单位字典的独立副本 |
| `q.copy()` / `Quantity(q)` | 独立副本 |

转换单位不会改变原对象。内部运算保留浮点精度，显示时才舍入。
省略 `significance` 时默认 15 位；可通过 `q.significance = 4` 调整显示精度。
乘除取较少有效数字位数，加减按较粗的末位精度处理；这不等同于不确定度传播。

## 单位写法

- 乘除：`kg*m/s2`、`N/m^2`、`1/s`、`/s`；`·` 可代替 `*`。
- 括号：`(m/s)**2`、`J/(m/s)`，也接受中文括号。
- 指数：`m2`、`m^2`、`m**2`、`s-2`、`m0.5`。分数指数请先换成小数，或用物理量乘方。
- 微米：`um`、`μm`、`µm`；欧姆：`ohm`、`omega`、`Ω`。
- 常用 SI 导出单位：`N`、`J`、`Pa`、`W`、`V`、`C`、`F`、`T`、`H`、`Wb`、`S` 等。
- 其他支持项包括 `eV`、`MeV`、`g`、`mg`、`u`（原子质量单位）、`min`、`h`，以及 `c`（光速单位）。

单位名称区分大小写。完整单位优先于词头，`h` 表示小时，`mg` 表示毫克。
多个单位之间必须写乘除号，不能用空格或紧邻书写代替。
摄氏度、华氏度的偏移转换暂不支持，请先换成 K，并区分温度与温差。
拼写错误、不完整表达式及未识别字符会报错，不会静默跳过。

自定义符号需显式启用，且保持名称原样，不自动猜测词头：

```python
from CwU import Q

count = Q(12, "count", allow_unknown_units=True)
print((count / Q(2, "s")).get_str("count/s"))  # 6.00000000000000 count/s
```

## 显示设置

```python
from CwU import Q

with Q.settings(use_scientific_notation=True):
    Q(-1200, significance=3).show()  # -1.20e3
    Q(1e-20, significance=3).show()  # 1.00e-20

Q.configure(use_significance=False)  # 持续设置；不改变计算值
Q.configure(use_significance=True)
```

三个全局开关为 `use_significance`、`use_scientific_notation`、`use_natural_units`。
旧写法 `Quantity.use_scientific_notation = True` 仍支持，并检查布尔类型；
不支持在单个实例上赋值。`settings()` 退出时恢复设置，包括异常退出；它不隔离并发线程。

## 自然单位制

```python
from CwU import Q, c, me

with Q.settings(use_natural_units=True, use_scientific_notation=True):
    mass = Q(1, "kg")
    energy = mass * c**2       # 也可与切换前已创建的常量运算
    energy.show("MeV")

si_mass = mass.to_si()
natural_mass = me.to_natural()
```

每个对象记录自己的单位制，切换设置不重新解释已有数值。
混合单位制运算将右侧对象转换到左侧单位制；指定目标单位的取值不受当前全局设置影响。
自然单位表示保留 `h_`、`c`、`k` 符号，不把它们自动当作无量纲数 1。
转换仍使用浮点数，极端数值组合可能上溢或下溢。

## 与旧版本的关系

- `legacy/` 保存 GitHub 上的 2024 年旧代码、说明，以及原始本地版 `CwU-0.260504.py`。
- 原先的 `from Quantity import Quantity` 应改为 `from CwU import Quantity`。
- `SN`、`Unit`、`Data` 旧接口没有合并进新版，旧文件保持归档状态，含已知缺陷。
- 本地版的 `get_value()`、`get_str()`、`show()`、主要常量名称和类开关写法继续支持。
- 有单位的量与非零普通数字相加减现在会报错；零作为加法初始值受支持，因此可以用 `sum()`。
- 常量表沿用本地版本的测定值；`mu0 = 4π×10⁻⁷ H/m` 等近似关系本轮没有校准。

详见 [CHANGELOG.md](CHANGELOG.md)。

## 维护与本地使用

推荐把仓库克隆到固定目录，把其中的 `CwU.py` 作为唯一维护源文件：

```bash
git clone https://github.com/YiXi-Rain/CfP.git
cd CfP
python -m unittest discover -s tests -v
```

后续在该目录修改、验证后手动提交。更新前先提交或保存本地修改，再执行 `git pull --ff-only`。
其他计算目录可复制单文件使用；对副本的修改应回到维护源文件中整理，避免形成多个长期分支。
稳定版本合并后可按 `__version__` 创建同名标签，例如 `v0.261016`。

测试仅依赖标准库，运行单文件不需要下载 `tests/` 或 `legacy/`。
