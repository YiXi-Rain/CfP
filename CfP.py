# coding: UTF-8
"""
Project: CfP--Calculation for Physics
Feature: work with dimensions & scientific notation
version: 0.3
"""
precision = 14  # 浮点运算时总会出现诸如.000000000000001/.999999999998的结果，利用参数precision配合函数round消除


class SN:  # SN即科学计数法scientific notation
    def __init__(self, value, significant=precision, index=None):
        # 值value
        self.__value = value
        # 有效数字significant
        if significant < 1:
            significant = precision
        elif significant > precision:
            significant = precision
        self.__significant = significant
        # 符号sign
        if value >= 0:
            self.__sign = 1
        else:
            self.__sign = -1
        # 指数index&系数coefficient
        self.__index_change = 0
        self.__coefficient = abs(value)
        self.__index = 0
        if value != 0:
            while self.__coefficient / 10 >= 1:  # 系数大于等于10时的处理
                self.__index += 1
                self.__coefficient = self.__coefficient / 10
            while self.__coefficient * 10 < 10:  # 系数小于1时的处理
                self.__index -= 1
                self.__coefficient = self.__coefficient * 10
            # 保留规定有效数字
            self.__set_sig(significant)
            if index != None:  # 指定指数时，进行额外处理
                self.set_index(index)
                self.__index = index
        else:  # 值为零时的处理
            self.__index = index
            self.__coefficient = 0.0  # 确保coefficient为浮点数

    def __str__(self):
        return str(self.__value)

    def __neg__(self):
        return -self.__value

    def __abs__(self):
        return abs(self.__value)

    def __pos__(self):
        return self.__value

    def __add__(self, other):
        if type(other) == SN:
            return self.__value + other.__value
        else:
            return self.__value + other

    def __sub__(self, other):
        if type(other) == SN:
            return self.__value - other.__value
        else:
            return self.__value - other

    def __mul__(self, other):
        if type(other) == SN:
            return self.__value * other.__value
        else:
            return self.__value * other

    def __pow__(self, power, modulo=None):
        return self.__value ** power

    def __truediv__(self, other):
        if type(other) == SN:
            return self.__value / other.__value
        else:
            return self.__value / other

    def __round__(self, n=None):
        return round(self.__value)

    def str(self):  # 以str返回coefficient&index
        string = str(self.__coefficient)
        if not self.__index_change:
            string += "0" * (1 + self.__significant - len(string))
        if self.__index == 0:
            return string
        else:
            return string + f"e{self.__index}"

    def tuple(self):
        return self.__coefficient, self.__index

    def __set_sig(self, significant):  # 设置有效数字位数为n，只能用于未设置index的SN实例
        if significant > self.__significant:
            significant = self.__significant
        elif significant < 1:
            significant = self.__significant
        self.__value = self.__round_check(significant) * 10 ** self.__index  # value有效数字比设定多一位
        self.__round_check(significant - 1)
        self.__significant = significant

    def __round_check(self, n):
        self.__coefficient = round(abs(self.__coefficient), n)
        if self.__coefficient / 10 >= 1:  # 上一步round存在进位可能性，需检验有效数字位数
            self.__index += 1
            self.__coefficient = self.__coefficient / 10
        self.__coefficient = self.__sign * round(self.__coefficient, n)
        return self.__coefficient

    def set_index(self, index):
        change = index - self.__index
        self.__coefficient = self.__coefficient * 10 ** -change
        self.__index = index
        self.__index_change += change

    def set_sig(self, significant):
        if not self.__index_change:
            self.__set_sig(significant)
        else:
            re = self.__index
            self.set_index(self.__index - self.__index_change)
            self.set_sig(significant)
            self.set_index(re)

    def sig(self):
        return self.__significant

    def ind(self):
        return self.__index


def change_sign(string):
    for j in range(len(string)):
        if string[j] == "/":
            string = string[:j] + "*" + string[j + 1:]
        elif string[j] == "*":
            string = string[:j] + "/" + string[j + 1:]
    return string


mul_dic = {'Y': '1e24', 'Z': '1e21', 'E': '1e18', 'P': '1e15', 'T': '1e12', 'G': '1e9', 'M': '1e6', 'k': '1e3',
           'h': '1e2', 'da': '1e1', 'd': '1e-1', 'c': '1e-2', 'm': '1e-3', 'μ': '1e-6', 'n': '1e-9', 'p': '1e-12',
           'f': '1e-15', 'a': '1e-18', 'z': '1e-21', 'y': '1e-24'}
dim_letter = "mesgclrVJAPKNHCFTWΩ℃"
dim_dic = {'eV': ('1.6e-19', '*J'), 'J': ('1e3', '*g*m*m/s/s'), 'Hz': ('1', '/s'), 'N': ('1e3', '*g*m/s/s'),
           'V': ('1', '*J/A/s'), 'C': ('1', '*A*s')}


class Quantity:
    """物理量类, 单位采用m g s A K mol cd"""

    def __init__(self, value: float, dimension: str = "", significant=precision, index=None):
        """物理量的值|[单位|有效数字|指数|]"""
        self.__value = SN(value)  # 物理量的值
        self.__dim = []  # 物理量的单位
        self.set_dim(dimension)  # 处理单位

    def __str__(self):
        return self.__str()

    def __pos__(self):
        return self

    def __neg__(self):
        return Quantity(-self.__value, self.__str_dim(), self.sig(), self.ind())

    def __add(self, other):
        if self.__dim == other.__dim:
            other.set_index(self.ind())
            str1 = str(abs(self.__value.tuple()[0]))
            str2 = str(abs(other.__value.tuple()[0]))
            sig = self.sig()
            if len(str1) > len(str2):
                sig -= len(str1) - len(str2)
            return Quantity(self.__value + other.__value, self.__str_dim(), sig)
        else:
            raise ValueError("！！不同量纲的物理量不能相加减！！")

    def __add__(self, other):
        if type(other) == Quantity:
            if abs(self.__value) >= abs(other.__value):
                return self.__add(other)
            else:
                return other.__add(self)
        else:
            return Quantity(self.__value + other)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        if type(other) == Quantity:
            return Quantity(self.__value * other.__value, self.__str_dim() + other.__str_dim(),
                            min(self.sig(), other.sig()))
        else:
            return Quantity(self.__value * other, self.__str_dim(), self.sig())

    def __truediv__(self, other):
        if type(other) == Quantity:
            return Quantity(self.__value / other.__value, self.__str_dim() + change_sign(other.__str_dim()),
                            min(self.sig(), other.sig()))
        else:
            return Quantity(self.__value / other, self.__str_dim(), self.sig())

    def __str_dim(self):  # 返回用str表示的单位
        string = ""
        for i in range(len(self.__dim)):
            n = self.__dim[i][1]
            while n > 0:
                string += "*" + self.__dim[i][0]
                n -= 1
            while n < 0:
                string += "/" + self.__dim[i][0]
                n += 1
        return string

    def __str(self, dim: str = ""):  # 返回用str表示的物理量(value&dimension)
        if not dim:
            string = self.__str_dim()
            if string.startswith("*"):
                string = string[1:]
            string = self.__value.str() + string
            return string
        else:
            new = self / Quantity(1, dim)
            if dim.startswith("*"):
                dim = dim[1:]
            return new.__value.str() + dim + new.__str_dim()

    def set_dim(self, dimension):
        if dimension:
            value = str(self.__value)
            for i in mul_dic:  # 处理单位的倍数
                n = dimension.find(i)
                while n != -1:
                    try:
                        if dimension[n + len(i)] in dim_letter:
                            value += dimension[n - 1] + mul_dic[i]
                            dimension = dimension[:n] + dimension[n + len(i):]
                        n = dimension[n + 1:].find(i)
                        if n != -1:
                            n += n + 1
                    except IndexError:
                        n = -1
            if not (dimension.startswith("/") or dimension.startswith("*")):
                dimension = "*" + dimension
            for i in dim_dic:  # 转换为基本单位（用g代替kg）
                n = dimension.find(i)
                while n != -1:
                    string = dim_dic[i][1]
                    if dimension[n - 1] == "*":
                        value += "*" + dim_dic[i][0]
                    else:
                        value += "/" + dim_dic[i][0]
                        string = change_sign(string)
                    dimension = dimension[:n - 1] + string + dimension[n + len(i):]
                    n = dimension.find(i)
            length = len(dimension) - 1
            while length > 0:  # 用list储存单位
                length -= 1
                if (dimension[length] == "/") or (dimension[length] == "*"):  # 发现"/"or"*"
                    if dimension[length] == "/":
                        a = -1
                    else:
                        a = 1
                    dim = dimension[length + 1:]
                    for i in self.__dim:
                        if i[0] == dim:
                            i[1] += a
                            break
                    else:
                        self.__dim.append([dim, a])
                    dimension = dimension[:length]
                    length -= (len(dim) - 1)
            lenth = len(self.__dim)  # 检查应该约去的单位
            t = 0
            while t < lenth:
                if self.__dim[t][1] == 0:
                    del self.__dim[t]
                    lenth -= 1
                else:
                    t += 1
            self.__value = SN(eval(value), self.sig(), self.ind())
            if self.__dim:  # 对单位排序
                self.__dim.sort(key=lambda x: (x[0], x[1]), reverse=False)

    def set_index(self, index):
        self.__value.set_index(index)

    def set_sig(self, significant):
        self.__value.set_sig(significant)

    def sig(self):
        return self.__value.sig()

    def ind(self):
        return self.__value.ind()

    def valuetuple(self):
        return self.__value.tuple()

    def value(self):
        return +self.__value

    def dim(self):
        return self.__str_dim()

    def show(self, dim: str = ""):
        string = self.__str(dim)
        print(string)
        return string
