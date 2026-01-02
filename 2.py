from turtle import *
from random import *

def HSB2RGB(hues):
    """将色相值(0-100)转换为RGB颜色值(0-1范围)"""
    hues = hues * 3.59  # 100转成359范围
    rgb = [0.0, 0.0, 0.0]
    i = int(hues/60) % 6
    f = hues/60 - i
    if i == 0:
        rgb[0] = 1; rgb[1] = f; rgb[2] = 0
    elif i == 1:
        rgb[0] = 1 - f; rgb[1] = 1; rgb[2] = 0
    elif i == 2:
        rgb[0] = 0; rgb[1] = 1; rgb[2] = f
    elif i == 3:
        rgb[0] = 0; rgb[1] = 1 - f; rgb[2] = 1
    elif i == 4:
        rgb[0] = f; rgb[1] = 0; rgb[2] = 1
    elif i == 5:
        rgb[0] = 1; rgb[1] = 0; rgb[2] = 1 - f
    return rgb

def snow():
    """绘制雪花图形"""
    # 生成雪花
    hideturtle()  # 隐藏海龟光标
    pensize(2)    # 设置画笔粗细为2
    speed(100)    # 设置绘制速度为最快(100)

    # 绘制100片雪花
    for i in range(100):
        # 为每片雪花生成随机颜色
        r = random()
        g = random()
        b = random()
        pencolor(r, g, b)

        # 将画笔移动到随机位置
        penup()  # 抬起画笔
        setx(randint(-350, 350))  # 设置x坐标在-350到350之间
        sety(randint(1, 270))     # 设置y坐标在1到270之间
        pendown()  # 放下画笔

        # 绘制单朵雪花
        dens = randint(8, 12)       # 雪花花瓣数量
        snowsize = randint(10, 14)  # 雪花花瓣长度

        # 绘制花瓣
        for j in range(dens):
            forward(snowsize)   # 向前移动
            backward(snowsize)  # 向后移动回到原点
            right(360/dens)     # 旋转角度，绘制下一个花瓣

def ground():
    """绘制地面效果"""
    hideturtle()  # 隐藏海龟光标
    speed(100)    # 设置绘制速度为最快

    # 绘制400个地面元素
    for i in range(400):  # 生成地面
        pensize(randint(5, 10))  # 设置随机画笔粗细

        # 设置随机起始位置
        x = randint(-400, 350)
        y = randint(-280, -1)

        # 根据y坐标计算颜色(模拟远近效果)
        # y值越小(越靠下)，颜色值越大(越亮)
        r = -y / 280
        g = -y / 280
        b = -y / 270

        # 确保颜色值不超过1
        r = min(r, 1.0)
        g = min(g, 1.0)
        b = min(b, 1.0)

        pencolor(r, g, b)  # 设置画笔颜色

        # 移动到指定位置并绘制线段
        penup()      # 抬起画笔
        goto(x, y)   # 移动到指定位置
        pendown()    # 放下画笔
        forward(randint(40, 100))  # 向前绘制随机长度的线段

def rainbow():
    """绘制彩虹效果"""
    hues = 0.0       # 初始化色相值
    color(1, 0, 0)   # 设置初始颜色为红色

    # 绘制彩虹
    hideturtle()     # 隐藏海龟光标
    speed(100)       # 设置绘制速度为最快
    pensize(3)       # 设置画笔粗细为3

    # 移动到起始位置
    penup()          # 抬起画笔
    goto(-400, -300) # 移动到画布左下角附近
    pendown()        # 放下画笔

    right(110)       # 向右旋转110度，调整绘制方向

    # 绘制100个弧线段，逐渐改变颜色
    for i in range(100):
        circle(1000)   # 绘制大圆弧(半径1000)
        right(0.13)    # 每次绘制后微调角度
        hues = hues + 1  # 增加色相值
        rgb = HSB2RGB(hues)  # 将色相转换为RGB颜色
        color(rgb[0], rgb[1], rgb[2])  # 设置新的画笔颜色

    penup()  # 绘制完成后抬起画笔

def main_snow():
    """主雪景绘制函数"""
    # 设置画布窗口
    setup(800, 600, 0, 0)  # 创建800x600像素的窗口，位置在屏幕(0,0)

    tracer(False)  # 关闭动画效果，一次性绘制所有图形

    bgcolor("black")  # 设置背景色为黑色

    # 调用绘制函数
    snow()    # 绘制雪花
    ground()  # 绘制地面

    tracer(True)  # 开启动画效果

    mainloop()  # 进入事件循环，保持窗口打开

def main_rainbow():
    """主彩虹绘制函数"""
    # 设置画布窗口
    setup(800, 600, 0, 0)  # 创建800x600像素的窗口，位置在屏幕(0,0)

    bgcolor((0.8, 0.8, 1.0))  # 设置背景为淡蓝色

    tracer(False)  # 关闭动画效果

    rainbow()  # 绘制彩虹

    # 输出文字
    goto(100, -100)  # 移动画笔到文字位置
    pendown()        # 放下画笔(虽然这里不需要绘制)
    color("red")     # 设置文字颜色为红色
    write("Rainbow", align="center",
          font=("Script MT Bold", 80, "bold"))  # 绘制文字

    tracer(True)  # 开启动画效果

    mainloop()  # 进入事件循环，保持窗口打开

# =========== 主程序循环 ===========
# 这是一个无限循环，直到用户输入666才会退出
while True:
    # 显示菜单选项
    print("如果你想看一片雪景，请输入1; 如果你想看一个彩虹，请输入2.")
    print("如果你想结束的话，请输入666.")

    # 获取用户输入并转换为整数
    num = int(input("请输入: "))

    # 根据用户选择执行相应操作
    if num == 1:
        # 用户选择1：显示雪景
        main_snow()  # 调用主雪景绘制函数
    elif num == 2:
        # 用户选择2：显示彩虹
        main_rainbow()  # 调用主彩虹绘制函数
    elif num == 666:
        # 用户选择666：退出程序
        print("程序结束")
        print("23101020204刘文昊")
        break  # 跳出循环，结束程序
    else:
        # 用户输入其他数字：提示错误
        print("输入错误")

