# coding: UTF-8
from SN import SN
from Unit import Unit

"""
Project: CfP--Calculation for Physics
Feature: work with dimensions & scientific notation
version: 1.0
"""
units_mode = 0  # 0为SI基本单位模式,1为自然单位制模式,2为原子物理模式(看other_base和other_dic的第二个元素)
prefixes = {'Y': 1e24, 'Z': 1e21, 'E': 1e18, 'P': 1e15, 'T': 1e12, 'G': 1e9, 'M': 1e6, 'k': 1e3, 'h': 1e2, 'da': 1e1,
            'd': 1e-1, 'c': 1e-2, 'm': 1e-3, 'μ': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15, 'a': 1e-18, 'z': 1e-21,
            'y': 1e-24}  # SI词头
special = ('c', 'me', 'mp', 'mn', 'Pa', 'T', 'Gy', 'kat', 'k', 'm', 'kg', 'mol', 'cd')  # 特判表
standard_base = ("m", "kg", "s", "K", "A", "mol", "cd")  # SI的基本单位
standard_dic = {"c": (2.99792458e8, "m/s"), "me": (9.10938215e-31, "kg"), "mp": (1.672621637e-27, "kg"),
                "mn": (1.674927212e-27, "kg"), "u": (1.660538782e-27, "kg"), 'eV': (1.602176487e-19, 'J'),
                'e': (1.602176487e-19, 'C'), "ε": (8.854187817e-12, "F/m"), "k": (1.3806504e-23, "J/K"), 'rad': (1, ''),
                'Hz': (1, 's-1'), 'Pa': (1, 'N*m2'), 'F': (1, 'C/V'), 'C': (1, 's*A'), 'Ω': (1, 'V/A'), 'S': (1, 'A/V'),
                'T': (1, 'Wb/m2'), 'H': (1, 'Wb/A'), 'Wb': (1, 'V*s'), '°C': (1, 'K'), 'lx': (1, 'lm*m2'),
                'lm': (1, 'cd*sr'), 'sr': (1, ''), 'Bq': (1, 's-1'), 'Gy': (1, 'J/kg'), 'Sv': (1, 'J/kg'),
                'kat': (1, 'mol/s'), 'V': (1, 'W/A'), 'W': (1, 'J/s'), 'J': (1, 'N*m'), 'N': (1, 'kg*m/s2')}
other_bases = (("h_", "c", "k", "MeV", "A", "mol", "cd"), ("fm", "MeV", "s", "K", "A", "mol", "cd"))  # 自然单位制的基本单位
other_dicts = ({"K": (8.6173428e-11, "MeV"), "s": (1.51926758e21, "/MeV"), "m": (5.06773116e12, "/MeV"),
                "kg": (5.609589118e29, "MeV")}, {"m": (1e15, "fm"), "kg": (6.241509647e-18, "MeV*s2/fm2")})
# 自然单位制保留k h_ c {"K": (8.6173428e-11, "MeV/k"), "s": (1.51926758e21, "h_/MeV"),
# "m": (5.06773116e12, "c*h_/MeV"), "kg": (5.609589118e29, "MeV/c2")}


def trans_units(value, unit_list, base_units, dic):
    while True:  # 转换成SI Standard Units
        tem_units = ""
        n = len(unit_list)
        i = 0
        while i < n:
            unit = unit_list[i][0]
            power = unit_list[i][1]
            if unit in dic:  # 单位在单位换算字典里
                tem_units += "*(" + dic[unit][1] + ")" + str(power)
                value *= (dic[unit][0] ** power)
                n -= 1
                del unit_list[i]
            else:
                i += 1
        unit_list = (Unit(unit_list) * Unit(tem_units)).list_copy()
        for i in unit_list:
            if i[0] not in base_units:
                break
        else:
            break
    return value, unit_list


class Quantity:
    """物理量(标量)类, 单位默认采用SI基本单位m kg s A K mol cd。所有方法均不改变原来的值,且除show外return均不为None。"""

    def __init__(self, value, unit: str or Unit = "", sig=10, simple=False):
        """
        储存物理量的值(科学计数法)和单位(SI基本单位)
        :param value: 物理量的值
        :param unit: 物理量的单位
        :param sig: 值的有效数字位数
        """
        if simple:  # 简化生成模式
            self.sn = value
            self.unit = unit
        else:
            unit_list = Unit(unit).list_copy()
            for i in unit_list:  # 处理词头
                if i[0] == "g":  # 克的特判
                    value *= 1e-3 ** i[1]
                    i[0] = "kg"
                else:
                    for j in prefixes:  # 真正处理词头
                        if (i[0].startswith(j)) and (i[0] not in special):  # 首字母与词头重复的单位的特判
                            value *= (prefixes[j] ** i[1])
                            i[0] = i[0][len(j):]
                            break
            value, unit_list = trans_units(value, unit_list, standard_base, standard_dic)
            if units_mode:  # 其他单位制
                value, unit_list = trans_units(value, unit_list, other_bases[units_mode-1], other_dicts[units_mode-1])
            self.sn = SN(value, sig)
            self.unit = Unit(unit_list, True)

    def __str__(self):
        return str(self.sn) + self.unit.str_unit()

    def __pos__(self):
        return self

    def __neg__(self):
        return Quantity(-self.sn, self.unit, simple=True)

    def __add__(self, other):
        if type(other) is Quantity:
            return Quantity(self.sn + other.sn, self.unit + other.unit, simple=True)
        elif (type(other) is int) or (type(other) is float):
            if self.unit == "":
                return Quantity(self.sn + other, self.unit, simple=True)
            else:
                raise ValueError("!单位不同的物理量不能相加!")
        else:
            raise TypeError("!Quantity类实例只能与Quantity/int/float类实例相加减!")

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        if type(other) is Quantity:
            return Quantity(self.sn * other.sn, self.unit * other.unit, simple=True)
        elif type(other) is float or type(other) is int:
            return Quantity(self.sn * other, self.unit, simple=True)
        else:
            raise TypeError("!Quantity类实例只能与Quantity/int/float类实例相乘!")

    def __pow__(self, power, modulo=None):
        if power == 0:
            return Quantity(1)
        else:
            return Quantity(self.sn ** power, self.unit ** power, simple=True)

    def __truediv__(self, other):
        if type(other) is Quantity:
            return Quantity(self.sn / other.sn, self.unit / other.unit, simple=True)
        elif type(other) is float or type(other) is int:
            return Quantity(self.sn / other, self.unit, simple=True)
        else:
            raise TypeError("!Quantity类实例只能除以Quantity/int/float类实例!")

    def sig(self):
        return self.sn.sig

    def set_sig(self, sig):
        sn = self.sn.set_sig(sig)
        return Quantity(sn, self.unit, sig, True)

    def set_unit(self, unit_str=None, power=None):
        if unit_str is None:  # 没有规定单位
            if power is None:  # 采用科学计数法
                return self.sn.str_if_power() + self.unit.str_unit()
            else:
                return self.sn.str_if_power(power) + self.unit.str_unit()
        else:  # 规定单位
            tem = self / Quantity(1, unit_str)
            string = tem.unit.str_unit()
            if string:
                string += "*" + unit_str
            else:
                string += " " + unit_str
            if power is None:  # 采用默认输出,即-2~2量级不采用科学计数法,其他量级采用科学计数法
                return str(tem.sn) + string
            else:
                return tem.sn.str_if_power(power) + string

    def show(self, unit_str=None, power=None):
        print(self.set_unit(unit_str, power))


# 数学常数
pi = 3.141592653589793
e_base = 2.718281828459045
# 物理学常量
G = Quantity(6.67408e-11, "N*m*m/kg/kg", 6)
e = Quantity(1, "e")
k = Quantity(1.3806504e-23, "J/K", 8)
c = Quantity(1, "c", 9)
h = Quantity(6.62606896e-34, "J*s", 9)
h_ = h / 2 / pi
epsilon0 = Quantity(1, "ε", 10)
me = Quantity(1, "me", 9)
mp = Quantity(1, "mp", 10)
mn = Quantity(1, "mn", 9)
# 组合常数combined_constant简写cc
cc_h = h_ * c  # ℏc
cc_e = e * e / 4 / pi / epsilon0
alpha = cc_e / cc_h
Ee = me * c * c
Ep = mp * c * c

RH = alpha ** 2 * 0.5 * me * c / h


def bohr_v(n=1, z=1):
    return alpha * z / n * c


def bohr_r(n=1, z=1):
    return h_ * n / me / bohr_v(z, n)


def bohr_E(n=1, z=1):
    return -(RH * h * c / n**2)
