# coding: UTF-8
# interpreter: python 3.11
"""
作为原Quantity的补充, 提供更多支持的输入单位格式:
1.(m/s)**2
2.m*s-2
3.m-2s-2
.....
!!!单独处理单位时无法进行换算!!!
"""


def get_num(string: str, start: int = 0):  # 返回get到的数字和被转换成数字的字符串的长度
    """
    对给定字符串,从规定索引值位置开始,提取数字成分(包括"1/3"这样的计算式)
    :param string: 需要提取数字成分的字符串
    :param start: 提取数字成分的起始位置,该位置应该是数字成分
    :return: (int or float)提取的数字, (int)对应的字符串的长度
    """
    string = string[start:]  # 从索引值为start的位置开始提取数字
    n = 0  # 表示从start开始的n位都是数字的组成部分
    try:
        while True:
            if string[n] in "0123456789+-.":  # 数字
                n += 1
            elif string[n] in "*/":  # 数字计算表达式
                if string[n + 1] in "0123456789+-.":
                    n += 1
                else:
                    break
            else:
                break
    except IndexError:  # 一直到末尾都没法发现不是数字组成部分的字符
        n = len(string)
    try:
        return eval(string[:n]), n
    except SyntaxError:  # 可能为""，需要添加"1"之后再转为数字
        try:
            return eval(string[:n] + "1"), n
        except SyntaxError:  # 还有可能是eval("01")这样的报错
            string = string[:n]
            sign = ""
            if string.startswith("+") or string.startswith("-"):
                sign = string[0]
                string = string[1:]
            if string.startswith("0") and string[1] != ".":
                string = string[1:]
            return eval(sign + string), n
        # 当然还有可能出现其他报错，暂时考虑不完全，先不管了


def get_str(string, start=0):
    """
    对给定字符串,从规定索引值位置开始,提取非数字成分
    :param string: 需要提取非数字成分的字符串
    :param start: 提取非数字成分的起始位置,该位置应该是非数字成分
    :return: (str)提取的非数字成分, (int)对应的字符串的长度
    """
    string = string[start:]  # 从索引值为start的位置开始提取非数字成分
    n = 0  # 表示从start开始的n位都是非数字成分
    str0 = ""  # 储存提取出的非数字成分
    for n in range(len(string)):
        if string[n] in "0123456789+-.*/":  # 到达数字成分的位置
            break
        else:  # 属于非数字成分
            str0 += string[n]
    else:  # 如果触发了break,那么非数字成分的长度为n;如果没有触发break运行结束,n=n+1
        n += 1
    return str0, n


def str_unit(units_list: list):
    """
    处理list形式的单位,返回str形式的单位
    :param units_list:
    :return: str形式的单位(以"*"+"unit"+"power"的格式)
    """
    unit_str = ""
    for i in units_list:
        if i[0]:
            unit_str += "*" + i[0] + str(i[1])
        else:  # 无单位时,只加入数字而不加入"*"
            unit_str += str(i[1])
    return unit_str


def unit_list_check(unit_list: list):
    """
    检查并格式化unit_list
    :param unit_list: 列表形式的单位
    :return: 格式化后的list
    """
    n = len(unit_list)
    i = 0
    while i < n:  # 消除power为0的单位
        unit_list[i][1] = round(unit_list[i][1], 10)  # 消去python浮点预算的奇妙.9999999999,如果power是循环小数,留10位也能看出来
        if unit_list[i][1] == 0:
            del unit_list[i]
            n -= 1
        else:
            if unit_list[i][1] % 1 == 0:
                unit_list[i][1] = int(unit_list[i][1])
            i += 1
    unit_list.sort(key=lambda x: x[0], reverse=False)  # 单位排序，统一输出格式
    return unit_list


def list_unit(unit_str: str, num: int or float = 1):
    """
    处理str形式的单位,返回list形式的单位
    :param unit_str: 字符串形式的单位
    :param num: unit_str整体具有的power
    :return: 除0排序后的list形式的单位
    """
    unit_list = []
    while unit_str:  # unit_str内一定没有括号,按顺序处理单位即可
        sign = 1  # power默认不需要变号
        if unit_str.startswith("/"):  # 如果是"/",power要变号
            sign = -1
        elif not unit_str.startswith("*"):  # 补充略去的*
            unit_str = "*" + unit_str
        unit, length = get_str(unit_str, 1)
        num0, length0 = get_num(unit_str, length + 1)  # 上一语句start=1,所以相对于unit_str要+1
        unit_str = unit_str[length + length0 + 1:]  # 截去已经处理完的部分
        for i in range(len(unit_list)):
            if unit_list[i][0] == unit:
                unit_list[i][1] += num0 * sign * num
                break
        else:
            unit_list.append([unit, num0 * sign * num])
    return unit_list_check(unit_list)


def inner_bracket(unit_str):
    """
    按照"从内向外，从左向右"的顺序处理字符串中的括号
    :param unit_str: 需要处理的字符串
    :return: (str)处理一次括号后的新字符串, (bool)是否处理完毕所有括号
    """
    num = 0  # 标识还没有开始提取括号后的数字
    left = -1
    right = len(unit_str)
    for i in range(len(unit_str)):  # 寻找应该最优先处理的括号,即最紧邻的括号
        if unit_str[i] == "(":
            left = i
        elif unit_str[i] == ")":
            right = i
            break
    else:  # 没有找到")"才执行
        if left == -1:  # 没有括号需要处理
            return unit_str, True  # Bool值标识括号是否处理完毕
        else:  # 有"("但没有")"，应该在字符串末尾补全，同时在括号后补上数字1
            num = 1
    length = 0  # 此时被提取的数字在字符串中对应的长度为0
    if not num:  # 如果还没有开始提取括号后的数字
        num, length = get_num(unit_str, right + 1)  # 只有触发了break才会运行到这个语句，此时right一定有定义
    if unit_str[left - 1] == "/":  # 在括号左侧有/，说明power要变符号
        num = -num
    elif unit_str[left - 1] != "*":  # 补充括号左边省略的*
        unit_str = unit_str[:left] + "*" + unit_str[left:]
        left += 1  # 相应的括号索引值要+1
        right += 1  # 相应的括号索引值要+1
    tem = unit_str[left + 1:right]  # 拿出括号内的部分作为需要处理的最小单位单元
    new = str_unit(list_unit(tem, num))  # 处理最小单元,必须将列表转回字符串才方便后续的处理
    return unit_str[:left - 1] + new + unit_str[right + 1 + length:], False  # 不能确保括号处理完毕，所以返回False


def clear_bracket(unit_str: str):
    """
    用于去除字符串形式的单位中所有的括号
    :param unit_str: 字符串形式的单位
    :return: (str)格式化后的字符串形式的单位
    """
    unit_str = unit_str.replace(" ", "")  # 去除所有空格
    unit_str = unit_str.replace("−", "-")  # 将cha(8722)转换为cha(45)
    unit_str = unit_str.replace("·", "*")  # 将cha(183)转换为cha(42)
    unit_str = unit_str.replace("**", "")  # 将乘方转换为空
    unit_str = unit_str.replace("^", "")  # 将cha(94)转换为空
    accomplished = False
    while not accomplished:  # 处理括号
        unit_str, accomplished = inner_bracket(unit_str)
    return unit_str


class Unit:
    """处理字符串形式的单位,储存双层列表形式的单位。所有方法均不改变原来的值,且return均不为None"""
    def __init__(self, unit: str or list = "", simple: bool = False):
        """
        以列表(list)的形式储存单位,生成过程中一定调用unit_list_check完成了格式化
        :param unit: 字符串(str)形式的单位(简化生成模式下为list)
        :param simple: 是否开启简化生成模式
        """
        if simple:  # Notice: 因为list共享指针,所以使用simple模式时,输入的unit必须是临时的
            self.__list = unit
        else:
            if type(unit) is str:
                self.__list = list_unit(clear_bracket(unit))
            else:
                self.__list = list_unit(str_unit(unit))

    def __str__(self):
        return str_unit(self.__list)

    def __pos__(self):
        return self

    def __neg__(self):
        unit = self.list_copy()
        for i in range(len(unit)):
            unit[i][1] *= -1
        return Unit(unit, True)

    def __eq__(self, other):  # 要想办法保证所有Unit的list都是格式化的,不然就有写format方法的必要(貌似已经保证了)
        if type(other) is Unit:
            return self.__list == other.__list
        elif (not other) and (not self.__list):
            return True
        else:
            return False

    def __add__(self, other):
        if self == other:
            return self
        else:
            raise ValueError("!不同单位不能相加减!")

    def __sub__(self, other):
        return self + other

    def __mul__(self, other):
        if type(other) is Unit:
            unit = self.list_copy()
            n = len(unit)
            for j in range(len(other.__list)):
                i = 0
                while i < n:
                    if other.__list[j][0] == unit[i][0]:  # 如果other的第j+1个单位在self中
                        unit[i][1] += other.__list[j][1]
                        break
                    i += 1
                else:
                    unit.append(other.__list[j].copy())
                    n += 1
            return Unit(unit_list_check(unit), True)
        else:
            raise TypeError("!Unit类实例只能与Unit类实例相乘除!")

    def __pow__(self, power, modulo=None):
        unit = self.list_copy()
        for i in range(len(unit)):
            unit[i][1] *= power
        return Unit(unit_list_check(unit), True)

    def __truediv__(self, other):
        return self * -other

    def list_copy(self):
        tem_list = []
        for i in self.__list:
            tem_list.append(i.copy())
        return tem_list

    def str_unit(self):
        """重写外部的str_unit方法,使Quantity调用Unit并print的结果更好看"""
        unit_str = ""
        for i in self.__list:
            if i[1] == 1:
                unit_str += "*" + i[0]
            else:
                unit_str += "*" + i[0] + str(i[1])
        if unit_str:
            return " " + unit_str[1:]
        else:
            return unit_str
