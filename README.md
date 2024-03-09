# CfP: Calculation for Physics
lastest version: 1.1 (upload at 2024/3/10 CST)

# Introcution
This file is used to do culcating between physics quantities with their dimensions(maybe called units, I'm not good at English) and display the results in scientific notation if necessary.

# How to use
1. Assign the variable a value(necessary,in float or int) and a dimension(optional, in str, default="").
   You can also assign the length of significant numbers by setting "significant=". But I set 14 as the limit and default of sig.
   ------Class Quantity------
   Format: Quantity(value[, dimension="", significant=14, index=None])   (The attribution "index" seems meaningless after this update, but I'm afraid that it creates more bugs to delete it.)
   e.g.  h = Quantity(6.62606896e-34, "J*s", 9)
   Notice: Dimension is case sensitive.

2. Calculate.
   You can use class Quantity to calculate just as it is int or float.
   But NOTICE:
   2.1 Make sure Quantity is in the front if calculating with int or float.
       e.g.  a = h * 2  This sentence is OK.(I have defined "h" in line 12)
             a = 2 * h  This sentence will raise Error.
   2.2 Class Quantity is not supporting the calculations that turn the powers of its dimensions to fractions.
       e.g.  a = h ** 2 is OK.
             b = a ** 0.5 is OK.
             a = h ** 0.5 raises Error.

3. Display the result.
   Class Quantity has a function named "show". It prints and returns the value and dimensions.
   Format: Quantity.show([dim="", sn:bool])
   Explaination:
   3.1 "dim" means dimensions. You can appoint a dimension and the printing result will include it while other dimensions are SI base units. But "the power of 'dim' could just be 1".
       e.g. h.show() ---------→ 6.62606896e-34kg*m*m/s
            a.show() ---------→ 4.39047899e-67kg*kg*m*m*m*m/s/s
            h.show("J*s") ----→ 6.62606896e-34J*s
            a.show("J*s") ----→ 4.39047899e-67J*s*kg*m*m/s (I said "the power of 'dim' could just be 1". It is not difficult to understand, right?)
            a.show("J*J*s*s") → 4.39047899e-67J*J*s*s

   3.2 "sn" means whether the result must be in scientific notation. Virtually it is only effective when "dim" is not "".
       You may notice that the type of "sn" should be bool, but its default is None. In fact, if "dim" is not "", the default will be False. Otherwise the default is True.
       But restricted by PYTHON, if the value of Quantity is very small or large, the result is still in scientific notation even if you set "sn=False".
       e.g. a = Quantity(5.29, "fm", 3)  
            a.show() ----------→ 5.29e-15m
            a.show("pm") ------→ 0.00529pm
            a.show("pm", True) → 5.29e-3pm

# At the end
从上一版修到这一版大概用了2个小时
写这个README也写了2个小时……
ORZ英语不好是真的难受QAQ
