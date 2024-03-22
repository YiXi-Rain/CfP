# coding: UTF-8
from SN import SN
from Unit import Unit

"""
Project: CfP--Calculation for Physics
Feature: work with dimensions & scientific notation
version: 1.0
"""
NaturalUnit = False  # 是否启用自然单位制
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
natural_base = ("h_", "c", "k", "MeV", "A", "mol", "cd")  # 自然单位制的基本单位
natural_dic = {"K": (8.6173428e-11, "MeV/k"), "s": (1.51926758e21, "h_/MeV"), "m": (5.06773116e12, "c*h_/MeV"),
               "kg": (5.609589118e29, "MeV/c2")}  # standard向natural转换的对应关系


def str_unit(units_list: list):
    """重写Unit中的str_unit方法,使print Quantity时结果更好看"""
    unit_str = ""
    for i in units_list:
        if i[1] == 1:
            unit_str += "*" + i[0]
        elif i[1] % 1 == 0:
            unit_str += "*" + i[0] + str(int(i[1]))
        else:
            unit_str += "*" + i[0] + str(i[1])
    if unit_str:
        return " " + unit_str[1:]
    else:
        return unit_str


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
        unit_list = (Unit(unit_list) + Unit(tem_units)).list_copy()
        for i in unit_list:
            if i[0] not in base_units:
                break
        else:
            break
    return value, unit_list


class Quantity:
    """物理量(标量)类, 单位采用m kg s A K mol cd"""

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
            if NaturalUnit:  # 自然单位制
                value, unit_list = trans_units(value, unit_list, natural_base, natural_dic)
            self.sn = SN(value, sig)
            self.unit = Unit(unit_list, True)

    def __str__(self):
        return str(self.sn) + str_unit(self.unit.list)

    def __pos__(self):
        return self

    def __neg__(self):
        return Quantity(-self.sn, self.unit, simple=True)

    def __add__(self, other):
        if type(other) is Quantity:
            if self.unit == other.unit:
                return Quantity(self.sn + other.sn, self.unit, simple=True)
            else:
                raise TypeError("!单位不同的物理量不能相加减!")
        else:
            raise TypeError("!Quantity类实例只能与Quantity类实例相加减!")

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
        self.sn.set_sig(sig)

    def set_unit(self, unit_str=None):
        if unit_str == None:
            return str(self)
        else:
            tem = self / Quantity(1, unit_str)
            string = str_unit(tem.unit.list)
            if string:
                string = "*" + str_unit(tem.unit.list)
            return tem.sn.str() + " " + unit_str + string

    def show(self, unit_str=None):
        print(self.set_unit(unit_str))


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
mn = Quantity(939.565346, "MeV/c/c", 9)
# 组合常数combined_constant简写cc
cc_h = h_ * c  # ℏc
cc_e = e * e / 4 / pi / epsilon0
alpha = cc_e / cc_h
Ee = me * c * c
Ep = mp * c * c


def bohr_v(z=1, n=1):
    return alpha * z / n * c


def bohr_r(z=1, n=1):
    return h_ * n / me / bohr_v(z, n)
