# ROS + OpenCV 作业报告：红色小球场景变换与虚拟遥控

**任务一：** 设计多种场景，让红色小球在场景中运动并支持手动拖拽与自动弹跳  
**任务二：** 以红色小球位置作为虚拟遥控输入，控制 turtlesim 海龟运动

---

## 1. 系统结构

```
ball_scene_pub_node.py
  ├── 绘制场景背景 + 红球
  ├── 发布 ShowImage（供检测节点订阅）
  └── 本地显示科技感 HUD（坐标系 + 海龟轨迹）

ball_control_node.py
  ├── 订阅 ShowImage
  ├── HSV 检测红球位置
  └── 发布 /turtle1/cmd_vel → turtlesim
```

---

## 2. 关键文件

| 文件 | 作用 |
|---|---|
| [`scripts/ball_scene_pub_node.py`](./scripts/ball_scene_pub_node.py) | 场景生成、红球绘制、发布 `ShowImage`、本地 HUD 显示 |
| [`scripts/ball_control_node.py`](./scripts/ball_control_node.py) | 红球检测、速度映射、控制海龟 |
| [`launch/ball_control.launch`](./launch/ball_control.launch) | 一键启动全部节点 |

---

## 3. 关键步骤

### 3.1 启动配置

```xml
<!-- launch/ball_control.launch -->
<launch>
  <node pkg="turtlesim" type="turtlesim_node" name="turtlesim" output="screen"/>
  <node pkg="image_tran" type="ball_scene_pub_node.py" name="ball_scene_pub" output="screen"/>
  <node pkg="image_tran" type="ball_control_node.py" name="ball_control" output="screen"/>
</launch>
```

### 3.2 场景渲染与图像发布（任务一）

按键空格切换场景，`a` 键切换自动弹跳/手动拖拽模式。每帧将当前场景背景加红球合并后发布到 `ShowImage` 话题：

```python
# ball_scene_pub_node.py
if cached_scene_idx != scene_index:
    cached_scene_bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    SCENE_DRAWERS[scene_index](cached_scene_bg)
    cached_scene_idx = scene_index

pub_canvas = cached_scene_bg.copy()
draw_pub_ball(pub_canvas, ball_x, ball_y)
pub.publish(bridge.cv2_to_imgmsg(pub_canvas, "bgr8"))
```

鼠标拖球：点击红球范围内按住拖动，松开停止；同时关闭自动弹跳：

```python
def mouse_callback(event, x, y, flags, param):
    global ball_x, ball_y, dragging, auto_mode
    if event == cv2.EVENT_LBUTTONDOWN:
        if math.sqrt((x - ball_x)**2 + (y - ball_y)**2) < BALL_RADIUS + 15:
            dragging = True
            auto_mode = False
    elif event == cv2.EVENT_MOUSEMOVE and dragging:
        ball_x = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, x))
        ball_y = max(BALL_RADIUS, min(HEIGHT - BALL_RADIUS, y))
    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False
```

### 3.3 红球 HSV 检测（任务二）

红色在 HSV 色环两端，需两段阈值合并掩码：

```python
# ball_control_node.py
hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
lower_red1 = np.array([0, 100, 100]);   upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([160, 100, 100]); upper_red2 = np.array([180, 255, 255])
mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

### 3.4 位置映射为速度（虚拟遥控核心）

将红球相对画面中心的归一化偏移直接映射为海龟线速度和角速度：

```python
# ball_control_node.py
offset_x = (ball_x - center_x) / center_x   # 右正左负
offset_y = (center_y - ball_y) / center_y   # 上正下负

twist.linear.x  = offset_y * 2.0    # 上→前进，下→后退
twist.angular.z = -offset_x * 2.0  # 左→左转，右→右转
cmd_pub.publish(twist)
```

偏离中心越远，速度越大（最大 2.0 m/s），球回到中心区域时自动停止。

---

## 4. 运行步骤

```bash
# 终端 1
roscore

# 终端 2
cd ~/newbot_ws && source devel/setup.bash
roslaunch image_tran ball_control.launch
```

运行后出现 3 个窗口：
- **Ball Controller**：科技感 HUD，显示坐标映射、海龟轨迹和红球（支持拖拽）
- **Ball Remote Control**：红球检测结果，显示当前控制方向和速度
- **turtlesim**：海龟运动窗口

---

## 5. 运行结果

> 运行截图/录屏请放入 `results/` 目录，建议文件名如下：
>
> - `results/01_ball_controller_hud.png` — Ball Controller 窗口截图
> - `results/02_ball_remote_control.png` — 红球检测窗口截图
> - `results/03_turtle_trace.png` — 海龟运动轨迹截图
> - `results/demo.mp4` — 完整演示录屏

<!-- 有截图后取消注释并替换路径：
![Ball Controller HUD](./results/01_ball_controller_hud.png)
![Red Ball Detection](./results/02_ball_remote_control.png)
![Turtle Trace](./results/03_turtle_trace.png)
[演示视频](./results/demo.mp4)
-->
