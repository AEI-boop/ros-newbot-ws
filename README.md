# ros-newbot-ws

一个结合 **mbot 移动机器人建模 / Gazebo 仿真 / 键盘控制 / 图像实验** 的 ROS1 `catkin` 工作空间。

当前工作空间包含两类内容：

1. `mbot_*` 系列：移动机器人模型、Gazebo 场景、遥控脚本
2. `image_tran`：基于 OpenCV 的图像发布、场景生成、红球检测与 turtlesim 虚拟遥控实验

---

## 1. 目录结构

```text
newbot_ws/
├── .catkin_workspace
├── .gitignore
├── README.md
└── src/
    ├── CMakeLists.txt
    ├── image_tran/
    ├── mbot_description/
    ├── mbot_gazebo/
    └── mbot_teleop/
```

---

## 2. 包说明

### 2.1 `image_tran`

视觉实验包，结合 OpenCV 与 ROS 图像消息完成场景生成、红球检测、虚拟遥控等任务。

关键资料：

- `src/image_tran/REPORT_ball_virtual_remote.md:1`

从报告可知，这个包实现了：

- 红色小球场景生成
- 手动拖拽 / 自动弹跳模式
- HSV 红球检测
- 将红球位置映射为 turtlesim 速度控制

关键入口：

- `launch/ball_control.launch`
- `launch/ball_scene.launch`
- `launch/search.launch`
- `launch/start.launch`

关键脚本：

- `scripts/ball_scene_pub_node.py`
- `scripts/ball_control_node.py`
- `scripts/image_pub_node.py`
- `scripts/image_sub_node.py`
- `scripts/search_sub_node.py`

### 2.2 `mbot_description`

移动机器人模型描述包。

从 `src/mbot_description/package.xml:1` 可见，核心依赖是：

- `urdf`
- `xacro`

包含：

- 机器人 URDF / Xacro
- RViz 配置
- 传感器模型（camera / kinect / laser）
- 相关 mesh

### 2.3 `mbot_gazebo`

Gazebo 仿真包。

关键启动文件示例：

- `src/mbot_gazebo/launch/view_mbot_gazebo_empty_world.launch:1`
- `view_mbot_gazebo_play_ground.launch`
- `view_mbot_gazebo_room.launch`
- `view_mbot_with_camera_gazebo.launch`
- `view_mbot_with_kinect_gazebo.launch`
- `view_mbot_with_laser_gazebo.launch`

从 `src/mbot_gazebo/launch/view_mbot_gazebo_empty_world.launch:1` 可知，该包会：

1. 启动 Gazebo 空世界
2. 加载 `mbot_description` 中的机器人模型
3. 启动 `joint_state_publisher`
4. 启动 `robot_state_publisher`
5. 在 Gazebo 中生成机器人

### 2.4 `mbot_teleop`

键盘遥控包。

启动文件：

- `src/mbot_teleop/launch/mbot_teleop.launch:1`

该 launch 会启动：

- `mbot_teleop.py`

并设置：

- 线速度缩放 `0.1`
- 角速度缩放 `0.4`

---

## 3. 环境要求

建议环境：

- Ubuntu 20.04
- ROS Noetic
- Gazebo
- RViz
- OpenCV
- Python 3

---

## 4. 构建方式

```bash
cd ~/newbot_ws
catkin_make
source devel/setup.bash
```

---

## 5. 常见运行方式

### 5.1 Gazebo 空场景启动 mbot

```bash
roslaunch mbot_gazebo view_mbot_gazebo_empty_world.launch
```

### 5.2 Gazebo 房间场景

```bash
roslaunch mbot_gazebo view_mbot_gazebo_room.launch
```

### 5.3 带相机 / 激光 / Kinect 的仿真

```bash
roslaunch mbot_gazebo view_mbot_with_camera_gazebo.launch
roslaunch mbot_gazebo view_mbot_with_laser_gazebo.launch
roslaunch mbot_gazebo view_mbot_with_kinect_gazebo.launch
```

### 5.4 键盘控制

```bash
roslaunch mbot_teleop mbot_teleop.launch
```

### 5.5 红球虚拟遥控实验

根据 `src/image_tran/REPORT_ball_virtual_remote.md:111` 的说明：

```bash
roscore
cd ~/newbot_ws && source devel/setup.bash
roslaunch image_tran ball_control.launch
```

运行后会出现：

- Ball Controller
- Ball Remote Control
- turtlesim

---

## 6. image_tran 实验说明

`image_tran` 更偏向课程实验与作业实现，当前重点内容包括：

- 红球检测
- 场景切换
- 鼠标拖拽控制
- 海龟虚拟遥控
- 图像发布 / 订阅示例

报告文件：

- `src/image_tran/REPORT_ball_virtual_remote.md:1`

如果你想快速理解该包，建议优先读这份报告，再看对应 launch 和 scripts。

---

## 7. 适合的使用方式

这个工作空间适合两条路线：

### 路线 A：移动机器人仿真

1. 启动 `mbot_gazebo`
2. 观察模型与传感器配置
3. 启动 `mbot_teleop`
4. 手动控制机器人

### 路线 B：图像处理与虚拟遥控

1. 启动 `image_tran` 的 ball control 实验
2. 观察 OpenCV 检测流程
3. 将视觉结果映射为运动控制

---

## 8. 常见问题

### 8.1 Gazebo 中机器人不显示

检查：

- 是否执行了 `source devel/setup.bash`
- `robot_description` 是否正确加载
- Gazebo / xacro 相关依赖是否已安装

### 8.2 键盘控制无响应

检查：

- 是否已有节点订阅 `/cmd_vel`
- 当前终端是否聚焦在 teleop 窗口
- 仿真是否已启动成功

### 8.3 图像实验窗口不弹出

检查：

- 本地图形环境是否正常
- OpenCV GUI 支持是否可用
- 是否直接在纯无头环境中运行

---

## 9. 关键文件索引

- 图像实验报告：`src/image_tran/REPORT_ball_virtual_remote.md:1`
- Gazebo 启动：`src/mbot_gazebo/launch/view_mbot_gazebo_empty_world.launch:1`
- 键盘遥控：`src/mbot_teleop/launch/mbot_teleop.launch:1`
- 模型依赖：`src/mbot_description/package.xml:1`
