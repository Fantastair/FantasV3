import fantas

# 创建窗口
window = fantas.Window(
    fantas.WindowConfig(
        title="Hello, Fantas!",
        window_size=(800, 600),
    )
)

# 创建渐变背景
background = fantas.LinearGradientLabel(
    rect=fantas.Rect((0, 0), window.size),
    start_color=fantas.Color('red'),
    end_color=fantas.Color('blue'),
    start_pos=(0, 0),
    end_pos=window.size
)
window.append(background)

# 设置默认文本样式
fantas.DEFAULTTEXTSTYLE.font = fantas.fonts.DEFAULTSYSFONT
fantas.DEFAULTTEXTSTYLE.size = 90
# 创建文本
text = fantas.Text(
    text="好好学习\n天天向上",
    rect=fantas.Rect(0, 0, 600, 300),
    align_mode=fantas.AlignMode.CENTER,
)
text.rect.center = background.rect.center  # 将文本中心对齐到背景中心
window.append(text)

# 启动窗口主循环
window.mainloop()
