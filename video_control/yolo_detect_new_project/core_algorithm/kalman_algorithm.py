import cv2

import numpy as np



class Kalman2DTracker:

    """

    二维目标追踪卡尔曼滤波器

    用于平滑 YOLO 检测框的中心坐标 (x, y)，并在目标短暂丢失时提供位置预测。

    """

    def __init__(self):

        # 4 个状态变量 [x, y, dx, dy], 2 个测量变量 [x, y]

        self.kf = cv2.KalmanFilter(4, 2)

       

        # 测量矩阵 H: 我们只能直接“看到”位置 x 和 y，看不到速度 dx, dy

        self.kf.measurementMatrix = np.array([

            [1, 0, 0, 0],

            [0, 1, 0, 0]

        ], np.float32)



        # 状态转移矩阵 F: 描述目标如何运动。这里假设匀速直线运动模型

        # x_new = x + dx, y_new = y + dy

        self.kf.transitionMatrix = np.array([

            [1, 0, 1, 0],

            [0, 1, 0, 1],

            [0, 0, 1, 0],

            [0, 0, 0, 1]

        ], np.float32)



        dt = 0.01 # 假设帧率为10fps

        self.kf.transitionMatrix = np.array([

            [1, 0, dt, 0],  # 这里变了

            [0, 1, 0, dt],  # 这里变了

            [0, 0, 1, 0],

            [0, 0, 0, 1]

        ], np.float32)





        # ---------------- 核心调参区 ----------------

        # 过程噪声协方差矩阵 Q: 系统对“匀速直线运动模型”的信任程度。

        # 值越小，系统越认为目标是在匀速走直线，轨迹越平滑，但对目标突然转向的响应越慢。

        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.5

       

        # 测量噪声协方差矩阵 R: 系统对“YOLO检测结果”的信任程度。

        # 值越大，系统越认为YOLO的结果有误差（噪点大），会更多地依赖上面的模型预测。

        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.08

        # --------------------------------------------



        self.is_initialized = False



    def update_and_output(self, current_x, current_y):

        """

        当 YOLO 检测到目标时调用。

        输入当前检测坐标，返回滤波平滑后的坐标。

        """

        # 防止第一次启动时，舵机从 (0,0) 猛转到目标位置

        if not self.is_initialized:

            # 强制初始化状态为当前测量的坐标，速度设为 0

            self.kf.statePre = np.array([[np.float32(current_x)], [np.float32(current_y)], [0], [0]], np.float32)

            self.kf.statePost = np.array([[np.float32(current_x)], [np.float32(current_y)], [0], [0]], np.float32)

            self.is_initialized = True

            return current_x, current_y



        # 1. 预测下一状态

        self.kf.predict()

       

        # 2. 用 YOLO 的实际测量值去纠正预测

        measurement = np.array([[np.float32(current_x)], [np.float32(current_y)]], np.float32)

        self.kf.correct(measurement)

       

        # 3. 返回纠正后的最优估计坐标

        estimated_state = self.kf.statePost

        return float(estimated_state[0, 0]), float(estimated_state[1, 0])



    def predict_only(self):

        """

        当 YOLO 丢失目标时（例如被短暂遮挡）调用。

        仅依靠历史速度预测目标现在应该在的位置。

        """

        if not self.is_initialized:

            return None, None # 还没初始化就丢了，直接放弃

           

        predicted_state = self.kf.predict()

        return float(predicted_state[0, 0]), float(predicted_state[1, 0])

       

    def reset(self):

        """目标丢失太久，重置滤波器"""

        self.is_initialized = False

       

       

if __name__ == "__main__":

    # 创建 Kalman2DTracker 实例

    tracker = Kalman2DTracker()



    # 假设这是从 YOLO 检测得到的一系列目标位置 (x, y)

    detections = [

        (100, 100),  # 第一帧检测到目标位置

        (102, 102),  # 第二帧检测到目标位置

        (105, 105),  # 第三帧检测到目标位置

        (110, 110),  # 第四帧检测到目标位置

        (120, 120),  # 第五帧检测到目标位置

        # 模拟目标短暂丢失，跟随进行预测

        None,         # 第六帧丢失

        None,         # 第七帧丢失

        (130, 130),  # 第八帧重新检测到目标位置

    ]



    # 模拟检测和预测过程

    for i, detection in enumerate(detections):

        if detection is not None:

            print(f"Frame {i+1} - Detection: {detection}")

            predicted_x, predicted_y = tracker.update(detection[0], detection[1])

            print(f"Frame {i+1} - Corrected (Filtered) Position: ({predicted_x}, {predicted_y})")

        else:

            print(f"Frame {i+1} - No Detection, Predicting...")

            predicted_x, predicted_y = tracker.predict_only()

            print(f"Frame {i+1} - Predicted Position: ({predicted_x}, {predicted_y})")

