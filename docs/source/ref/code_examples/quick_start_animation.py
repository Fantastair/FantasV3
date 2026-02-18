import fantas

window = fantas.Window(
    fantas.WindowConfig(
        title="Animate It!",
        window_size=(400, 300),
    )
)

# 纯色背景
background = fantas.ColorBackground(fantas.Color(0, 0, 0))
window.append(background)

# 来个小方块吧
block = fantas.Label(fantas.Rect(20, 20, 50, 50))
background.append(block)

# 动画1：让方块动起来
block_pos_kf = fantas.PointKeyFrame(
    block.rect,
    "center",
    fantas.Vector2(355, 255),
    fantas.CURVE_SMOOTH,
)
block_pos_kf.set_duration_ms(1000)
block_pos_kf.start()

# 动画2：让背景变色
background_color_kf = fantas.ColorKeyframe(
    background,
    "bgcolor",
    fantas.Color(255, 0, 0),
    fantas.CURVE_SMOOTH,
)
background_color_kf.set_duration_ms(1000)
background_color_kf.start()

window.mainloop()
