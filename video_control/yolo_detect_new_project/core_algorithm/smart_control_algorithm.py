class SmartControlAlgorithm:
    """智能控制算法类(简单纯线性外推算法，基础版本)"""
    # 注意，当前简单控制算法受视频帧率影响很大，
    # 主要依据速度：1，VSCODE NO IMAGE模式。 2：外接屏幕（非远程）直接视频控制模式
    def __init__(self): # 初始化函数
        
        self.SCREEN_WIDTH = 864
        self.SCREEN_HEIGHT = 640
        
        #SMART CONTROL 参数预先存储
        self.smart_last_target_center_x = self.SCREEN_WIDTH/2 # 上一帧目标中心x坐标
        self.smart_last_target_center_y = self.SCREEN_HEIGHT/2 # 上一帧目标中心y坐标
        self.smart_now_target_center_x = self.SCREEN_WIDTH/2 # 当前帧目标中心x坐标
        self.smart_now_target_center_y = self.SCREEN_HEIGHT/2 # 当前帧目标中心y坐标
    
    def update_smart_control_params(self,new_target_center_x,new_target_center_y):
        
        """更新SMART CONTROL 参数，根据测量得到的new_target_conter_x or y 写入，更新成员变量"""
        """这个参数更新只在 实际执行yolo_detect 轮次执行,YOLO检测到目标后，调用update_params更新参数"""
        
        self.smart_last_target_center_x = self.smart_now_target_center_x # 更新上一帧目标中心x坐标
        self.smart_last_target_center_y = self.smart_now_target_center_y # 更新上一帧目标中心y坐标
        self.smart_now_target_center_x = new_target_center_x # 更新当前帧目标中心x坐标
        self.smart_now_target_center_y = new_target_center_y # 更新当前帧目标中心y坐标
    
    def get_smart_control_params(self):
        """一个接口，返回成员变量，获取SMART CONTROL 参数"""
        return self.smart_last_target_center_x, self.smart_last_target_center_y, self.smart_now_target_center_x, self.smart_now_target_center_y
    
    def calculate_smart_control_target_center(self):
        """samrt_control核心算法，计算智能超前预估控制的目标中心坐标"""
        
        dx = self.smart_now_target_center_x - self.smart_last_target_center_x # 计算当前帧目标中心x坐标与上一帧目标中心x坐标的差值
        dy = self.smart_now_target_center_y - self.smart_last_target_center_y # 计算当前帧目标中心y坐标与上一帧目标中心y坐标的差值
        smart_predicted_target_center_x = self.smart_now_target_center_x + dx # 计算智能超前预估控制的目标中心x坐标
        smart_predicted_target_center_y = self.smart_now_target_center_y + dy # 计算智能超前预估控制的目标中心y坐标
        
        return smart_predicted_target_center_x, smart_predicted_target_center_y
    
 
    
#测试代码部分
if __name__ == "__main__":
    # 测试简单控制算法
    smart_control = SmartControlAlgorithm()
    # 模拟目标中心坐标更新
    smart_control.update_smart_control_params(100, 100)
    smart_control.update_smart_control_params(110,120)
    # 计算智能超前预估控制的目标中心坐标
    predicted_x, predicted_y = smart_control.calculate_smart_control_target_center()
    print(f"预测目标中心坐标: ({predicted_x:.1f}, {predicted_y:.1f})")