#!/usr/bin/env python3
# coding=utf-8
"""
Ball Controller - 科技感控制面板
- 发布图像：场景背景 + 红球（给远程控制窗口检测用，保持原样）
- 本地显示：科技感坐标系 + 海龟位姿实时映射 + 红球控制
"""
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image
from turtlesim.msg import Pose
from cv_bridge import CvBridge
import math
import time

# ========== 参数 ==========
WIDTH, HEIGHT = 640, 480
BALL_RADIUS = 22

# 坐标系绘图区域（本地 HUD 用）
MARGIN = 50
PLOT_X0, PLOT_Y0 = MARGIN, 40
PLOT_X1, PLOT_Y1 = WIDTH - MARGIN, HEIGHT - 55
PLOT_W = PLOT_X1 - PLOT_X0
PLOT_H = PLOT_Y1 - PLOT_Y0
TURTLE_MAX = 11.0

# ========== 全局状态 ==========
ball_x, ball_y = WIDTH // 2, HEIGHT // 2
dragging = False
auto_mode = False

turtle_x, turtle_y, turtle_theta = 5.5, 5.5, 0.0
turtle_linear, turtle_angular = 0.0, 0.0

trajectory = []
MAX_TRAIL = 600

scene_index = 0


def pose_callback(msg):
    global turtle_x, turtle_y, turtle_theta, turtle_linear, turtle_angular
    turtle_x = msg.x
    turtle_y = msg.y
    turtle_theta = msg.theta
    turtle_linear = msg.linear_velocity
    turtle_angular = msg.angular_velocity
    trajectory.append((msg.x, msg.y))
    if len(trajectory) > MAX_TRAIL:
        trajectory.pop(0)


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


def turtle_to_pixel(tx, ty):
    px = int(PLOT_X0 + (tx / TURTLE_MAX) * PLOT_W)
    py = int(PLOT_Y1 - (ty / TURTLE_MAX) * PLOT_H)
    return px, py


# ==================================================================
# 发布用场景背景（给 ball_control_node 检测用，保持原始风格）
# ==================================================================

def draw_scene_grass(canvas):
    for i in range(HEIGHT):
        g = int(100 + 60 * (i / HEIGHT))
        canvas[i, :] = (20, g, 15)
    cv2.rectangle(canvas, (40, 40), (WIDTH-40, HEIGHT-40), (255,255,255), 2)
    cv2.line(canvas, (WIDTH//2, 40), (WIDTH//2, HEIGHT-40), (255,255,255), 2)
    cv2.circle(canvas, (WIDTH//2, HEIGHT//2), 60, (255,255,255), 2)

def draw_scene_night(canvas):
    for i in range(HEIGHT):
        r = i / HEIGHT
        canvas[i, :] = (int(80-60*r), int(20-15*r), 5)
    np.random.seed(42)
    for _ in range(100):
        sx, sy = np.random.randint(0,WIDTH), np.random.randint(0,HEIGHT*2//3)
        br = np.random.randint(150,255)
        cv2.circle(canvas, (sx,sy), 1, (br,br,br-30), -1)
    np.random.seed(None)
    cv2.circle(canvas, (520,60), 30, (200,230,250), -1)

def draw_scene_desert(canvas):
    for i in range(HEIGHT):
        r = i / HEIGHT
        canvas[i, :] = (int(60*(1-r)), int(140+80*r), min(int(180+50*r),255))
    cv2.circle(canvas, (500,80), 40, (30,180,255), -1)

def draw_scene_ocean(canvas):
    for i in range(HEIGHT//2):
        r = i/(HEIGHT//2)
        canvas[i, :] = (int(200-80*r), int(180-60*r), int(100+50*r))
    for i in range(HEIGHT//2, HEIGHT):
        r = (i-HEIGHT//2)/(HEIGHT//2)
        canvas[i, :] = (int(160-80*r), int(100-60*r), 20)

def draw_scene_court(canvas):
    for i in range(HEIGHT):
        shade = 10 if (i//12)%2==0 else -10
        canvas[i, :] = (45+shade, 120+shade, 200+shade)
    cv2.rectangle(canvas, (30,30), (WIDTH-30,HEIGHT-30), (255,255,255), 2)
    cv2.circle(canvas, (WIDTH//2,HEIGHT//2), 55, (255,255,255), 2)

SCENE_DRAWERS = [draw_scene_grass, draw_scene_night, draw_scene_desert, draw_scene_ocean, draw_scene_court]
SCENE_NAMES = ["Grass", "Night", "Desert", "Ocean", "Court"]


def draw_pub_ball(canvas, x, y):
    """发布图像上的红球（简洁，方便检测）"""
    cv2.circle(canvas, (x, y), BALL_RADIUS, (0, 0, 220), -1)
    cv2.circle(canvas, (x-6, y-6), BALL_RADIUS//2, (60, 60, 255), -1)
    cv2.circle(canvas, (x-8, y-8), 3, (200, 200, 255), -1)


# ==================================================================
# 本地 HUD 显示（科技感坐标系）
# ==================================================================

CYAN = (255, 200, 0)
GLOW = (255, 230, 100)
DIM_CYAN = (140, 100, 0)
RED_GLOW = (80, 80, 255)
GREEN_GLOW = (100, 255, 180)
ORANGE = (50, 180, 255)
WHITE_DIM = (160, 170, 170)


def draw_hud_background(canvas, frame_count):
    """深色科技感背景"""
    canvas[:] = (15, 15, 20)
    # 扫描线效果
    for i in range(0, HEIGHT, 3):
        canvas[i, :] = np.clip(canvas[i].astype(np.int16) + 5, 0, 255).astype(np.uint8)

    # 四角装饰框
    L = 25
    for (cx, cy) in [(2,2),(WIDTH-2,2),(2,HEIGHT-2),(WIDTH-2,HEIGHT-2)]:
        dx = 1 if cx < WIDTH//2 else -1
        dy = 1 if cy < HEIGHT//2 else -1
        cv2.line(canvas, (cx, cy), (cx + dx*L, cy), CYAN, 1)
        cv2.line(canvas, (cx, cy), (cx, cy + dy*L), CYAN, 1)


def draw_hud_grid(canvas):
    """科技感坐标网格"""
    # 网格区域底色（微亮）
    overlay = canvas.copy()
    cv2.rectangle(overlay, (PLOT_X0, PLOT_Y0), (PLOT_X1, PLOT_Y1), (25, 25, 35), -1)
    cv2.addWeighted(overlay, 0.6, canvas, 0.4, 0, canvas)

    # 网格线
    for i in range(12):
        px = int(PLOT_X0 + (i / TURTLE_MAX) * PLOT_W)
        py = int(PLOT_Y1 - (i / TURTLE_MAX) * PLOT_H)
        color = DIM_CYAN if i % 5 != 0 else CYAN
        thickness = 1
        cv2.line(canvas, (px, PLOT_Y0), (px, PLOT_Y1), color, thickness)
        cv2.line(canvas, (PLOT_X0, py), (PLOT_X1, py), color, thickness)
        # 刻度
        cv2.putText(canvas, str(i), (px - 4, PLOT_Y1 + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, CYAN, 1)
        if i > 0:
            cv2.putText(canvas, str(i), (PLOT_X0 - 22, py + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, CYAN, 1)

    # 坐标轴
    cv2.line(canvas, (PLOT_X0, PLOT_Y1), (PLOT_X1 + 5, PLOT_Y1), CYAN, 2)
    cv2.line(canvas, (PLOT_X0, PLOT_Y0 - 5), (PLOT_X0, PLOT_Y1), CYAN, 2)
    cv2.arrowedLine(canvas, (PLOT_X1-5, PLOT_Y1), (PLOT_X1+18, PLOT_Y1), CYAN, 2, tipLength=0.5)
    cv2.arrowedLine(canvas, (PLOT_X0, PLOT_Y0+5), (PLOT_X0, PLOT_Y0-18), CYAN, 2, tipLength=0.5)
    cv2.putText(canvas, "X", (PLOT_X1+18, PLOT_Y1+5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, CYAN, 1)
    cv2.putText(canvas, "Y", (PLOT_X0-8, PLOT_Y0-20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, CYAN, 1)
    cv2.putText(canvas, "0", (PLOT_X0-14, PLOT_Y1+16), cv2.FONT_HERSHEY_SIMPLEX, 0.3, CYAN, 1)


def draw_hud_trail(canvas):
    """海龟运动轨迹（渐变发光）"""
    if len(trajectory) < 2:
        return
    for i in range(1, len(trajectory)):
        p1 = turtle_to_pixel(trajectory[i-1][0], trajectory[i-1][1])
        p2 = turtle_to_pixel(trajectory[i][0], trajectory[i][1])
        ratio = i / len(trajectory)
        alpha = int(50 + 205 * ratio)
        color = (int(alpha * 0.5), int(alpha * 0.8), 0)
        cv2.line(canvas, p1, p2, color, 1, cv2.LINE_AA)


def draw_hud_turtle(canvas, frame_count):
    """海龟位姿图标（带方向指示和脉冲圈）"""
    tpx, tpy = turtle_to_pixel(turtle_x, turtle_y)
    angle = -turtle_theta

    # 脉冲扩散圈
    pulse = int(15 + 8 * math.sin(frame_count * 0.1))
    cv2.circle(canvas, (tpx, tpy), pulse, (80, 120, 0), 1, cv2.LINE_AA)

    # 朝向三角形
    sz = 16
    p1 = (int(tpx + sz * math.cos(angle)),       int(tpy + sz * math.sin(angle)))
    p2 = (int(tpx + sz*0.5 * math.cos(angle+2.5)), int(tpy + sz*0.5 * math.sin(angle+2.5)))
    p3 = (int(tpx + sz*0.5 * math.cos(angle-2.5)), int(tpy + sz*0.5 * math.sin(angle-2.5)))
    pts = np.array([p1, p2, p3], np.int32)
    cv2.fillPoly(canvas, [pts], GREEN_GLOW)
    cv2.polylines(canvas, [pts], True, (200, 255, 220), 1, cv2.LINE_AA)

    # 朝向延长线
    ex = int(tpx + 35 * math.cos(angle))
    ey = int(tpy + 35 * math.sin(angle))
    cv2.arrowedLine(canvas, (tpx, tpy), (ex, ey), (80, 200, 120), 1, cv2.LINE_AA, tipLength=0.3)

    # 坐标标注
    cv2.putText(canvas, f"({turtle_x:.1f},{turtle_y:.1f})",
                (tpx + 18, tpy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.32, GREEN_GLOW, 1)


def draw_hud_ball(canvas, x, y):
    """HUD上的红球（发光效果）"""
    # 外发光
    cv2.circle(canvas, (x, y), BALL_RADIUS + 6, (0, 0, 80), 2, cv2.LINE_AA)
    cv2.circle(canvas, (x, y), BALL_RADIUS + 3, (0, 0, 120), 1, cv2.LINE_AA)
    # 球体
    cv2.circle(canvas, (x, y), BALL_RADIUS, (0, 0, 210), -1, cv2.LINE_AA)
    cv2.circle(canvas, (x-5, y-5), BALL_RADIUS//2, (50, 50, 255), -1)
    cv2.circle(canvas, (x-7, y-7), 3, (180, 180, 255), -1)


def draw_hud_control_vector(canvas, x, y):
    """从中心到球的控制向量线"""
    cx, cy = WIDTH // 2, (PLOT_Y0 + PLOT_Y1) // 2
    dist = math.sqrt((x - cx)**2 + (y - cy)**2)
    if dist < 10:
        return
    # 虚线效果
    steps = int(dist / 8)
    for i in range(steps):
        t1 = i / steps
        t2 = min((i + 0.5) / steps, 1.0)
        sx = int(cx + (x - cx) * t1)
        sy = int(cy + (y - cy) * t1)
        ex = int(cx + (x - cx) * t2)
        ey = int(cy + (y - cy) * t2)
        color = ORANGE if dist > 120 else (0, 255, 255)
        cv2.line(canvas, (sx, sy), (ex, ey), color, 1, cv2.LINE_AA)
    # 中心准星
    cv2.drawMarker(canvas, (cx, cy), CYAN, cv2.MARKER_CROSS, 12, 1)
    cv2.circle(canvas, (cx, cy), 6, DIM_CYAN, 1)


def draw_hud_info_panel(canvas, frame_count):
    """顶部和底部科技感信息面板"""
    # 顶部标题栏
    cv2.line(canvas, (0, 22), (WIDTH, 22), DIM_CYAN, 1)
    cv2.putText(canvas, "TURTLE TRACKING SYSTEM", (8, 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, CYAN, 1)
    # 帧计数闪烁点
    blink = (frame_count // 15) % 2
    if blink:
        cv2.circle(canvas, (WIDTH - 15, 11), 4, (0, 0, 255), -1)
    cv2.putText(canvas, "REC", (WIDTH - 48, 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 200), 1)

    # 底部信息栏
    bar_y = HEIGHT - 40
    cv2.line(canvas, (0, bar_y), (WIDTH, bar_y), DIM_CYAN, 1)

    # 位姿信息
    theta_deg = math.degrees(turtle_theta)
    cv2.putText(canvas, f"POS  X:{turtle_x:5.1f}  Y:{turtle_y:5.1f}",
                (10, bar_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.35, GLOW, 1)
    cv2.putText(canvas, f"HDG {theta_deg:6.1f}deg",
                (230, bar_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.35, GLOW, 1)
    cv2.putText(canvas, f"SPD {turtle_linear:+5.2f}",
                (390, bar_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.35, GREEN_GLOW, 1)
    cv2.putText(canvas, f"ROT {turtle_angular:+5.2f}",
                (520, bar_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.35, GREEN_GLOW, 1)

    # 操作提示
    mode_text = "AUTO" if auto_mode else "DRAG"
    cv2.putText(canvas, f"[{mode_text}]  SPC:Scene  A:Mode  R:Reset  [{SCENE_NAMES[scene_index]}]",
                (10, HEIGHT - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.30, WHITE_DIM, 1)


# ==================================================================

def pubBallScene():
    global ball_x, ball_y, scene_index, auto_mode

    rospy.init_node('ball_scene_pub', anonymous=True)
    pub = rospy.Publisher('ShowImage', Image, queue_size=10)
    rospy.Subscriber('/turtle1/pose', Pose, pose_callback)
    rate = rospy.Rate(30)
    bridge = CvBridge()

    cv2.namedWindow("Ball Controller")
    cv2.setMouseCallback("Ball Controller", mouse_callback)

    ball_vx, ball_vy = 3, 2
    frame_count = 0
    cached_scene_bg = None
    cached_scene_idx = -1

    rospy.loginfo("=== Ball Controller [HUD Mode] ===")

    while not rospy.is_shutdown():
        frame_count += 1

        # 自动弹跳
        if auto_mode and not dragging:
            ball_x += ball_vx
            ball_y += ball_vy
            if ball_x - BALL_RADIUS <= 0 or ball_x + BALL_RADIUS >= WIDTH:
                ball_vx = -ball_vx
            if ball_y - BALL_RADIUS <= 0 or ball_y + BALL_RADIUS >= HEIGHT:
                ball_vy = -ball_vy
            ball_x = max(BALL_RADIUS, min(WIDTH-BALL_RADIUS, ball_x))
            ball_y = max(BALL_RADIUS, min(HEIGHT-BALL_RADIUS, ball_y))
            if frame_count % 200 == 0:
                scene_index = (scene_index + 1) % len(SCENE_DRAWERS)
                cached_scene_idx = -1

        # ========== 1. 生成发布图像（场景背景 + 红球 → 远程控制窗口用） ==========
        if cached_scene_idx != scene_index:
            cached_scene_bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            SCENE_DRAWERS[scene_index](cached_scene_bg)
            cached_scene_idx = scene_index
        pub_canvas = cached_scene_bg.copy()
        draw_pub_ball(pub_canvas, ball_x, ball_y)
        pub.publish(bridge.cv2_to_imgmsg(pub_canvas, "bgr8"))

        # ========== 2. 生成本地 HUD 显示（科技感坐标系 + 海龟位姿） ==========
        hud = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        draw_hud_background(hud, frame_count)
        draw_hud_grid(hud)
        draw_hud_trail(hud)
        draw_hud_turtle(hud, frame_count)
        draw_hud_ball(hud, ball_x, ball_y)
        draw_hud_control_vector(hud, ball_x, ball_y)
        draw_hud_info_panel(hud, frame_count)

        cv2.imshow("Ball Controller", hud)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            scene_index = (scene_index + 1) % len(SCENE_DRAWERS)
            cached_scene_idx = -1
        elif key == ord('a'):
            auto_mode = not auto_mode
            rospy.loginfo(f"Mode: {'Auto' if auto_mode else 'Manual'}")
        elif key == ord('r'):
            ball_x, ball_y = WIDTH // 2, HEIGHT // 2
            trajectory.clear()
            rospy.loginfo("Reset")

        rate.sleep()

    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        pubBallScene()
    except rospy.ROSInterruptException:
        pass
