import cv2
import numpy as np

class Kalman2DTracker:
    """
    二维目标追踪卡尔曼滤波器 (已升维：恒定加速度模型)
    处理不规则、有加减速的运动目标。
    """
    def __init__(self):
        # 升维：6 个状态变量 [x, y, dx, dy, ddx, ddy], 2 个测量变量 [x, y]
        self.kf = cv2.KalmanFilter(6, 2)
        
        # 测量矩阵 H: (2x6) 我们依然只能直接“看到”位置 x 和 y
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0]
        ], np.float32)

        dt = 0.01 # 假设帧率为10fps (时间间隔)
        
        # 状态转移矩阵 F: (6x6) 引入加速度的运动学公式
        self.kf.transitionMatrix = np.array([
            [1, 0, dt, 0,  0.5*(dt**2), 0          ],
            [0, 1, 0,  dt, 0,           0.5*(dt**2)],
            [0, 0, 1,  0,  dt,          0          ],
            [0, 0, 0,  1,  0,           dt         ],
            [0, 0, 0,  0,  1,           0          ],
            [0, 0, 0,  0,  0,           1          ]
        ], np.float32)

        # ---------------- 核心调参区 ----------------
        # 过程噪声 Q: 升维后变成了 6x6 矩阵。
        # 如果目标运动非常“诡异/无规律”，可以适当调大这个矩阵的最后两个对角线值（加速度噪声）。
        self.kf.processNoiseCov = np.eye(6, dtype=np.float32) * 0.1
        
        # 测量噪声 R: 保持不变，代表对 YOLO 检测框的信任度
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1.0
        # --------------------------------------------

        self.is_initialized = False

    def update_and_output(self, current_x, current_y):
        if not self.is_initialized:
            # 初始化状态必须匹配 6 维列向量
            state = np.array([[np.float32(current_x)], [np.float32(current_y)], [0], [0], [0], [0]], np.float32)
            self.kf.statePre = state.copy()
            self.kf.statePost = state.copy()
            self.is_initialized = True
            return current_x, current_y

        # 1. 预测下一状态
        self.kf.predict()
        
        # 2. 用 YOLO 的测量值纠正
        measurement = np.array([[np.float32(current_x)], [np.float32(current_y)]], np.float32)
        self.kf.correct(measurement)
        
        # 3. 输出平滑后的坐标
        return float(self.kf.statePost[0, 0]), float(self.kf.statePost[1, 0])

    def predict_only(self):
        if not self.is_initialized:
            return None, None 
            
        predicted_state = self.kf.predict()
        return float(predicted_state[0, 0]), float(predicted_state[1, 0])
        
    def reset(self):
        self.is_initialized = False

# 测试脚本部分保持不变...