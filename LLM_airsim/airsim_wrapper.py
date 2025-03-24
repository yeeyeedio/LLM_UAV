#airsim_wrapper.py
import airsim  # AirSim 库，用于与 AirSim 模拟平台进行通信
import math  # 导入数学库
import numpy as np  # 导入 numpy 库

# 定义一个字典，映射物体名称到 Unreal Engine 中的对象名称
objects_dict = {
    "turbine1": "BP_Wind_Turbines_C_1",  # 风力涡轮机 1
    "turbine2": "StaticMeshActor_2",     # 风力涡轮机 2
    "solarpanels": "StaticMeshActor_146", # 太阳能面板
    "crowd": "StaticMeshActor_6",        # 人群
    "car": "StaticMeshActor_10",          # 汽车
    "tower1": "SM_Electric_trellis_179",  # 电塔 1
    "tower2": "SM_Electric_trellis_7",    # 电塔 2
    "tower3": "SM_Electric_trellis_8",    # 电塔 3
}


class AirSimWrapper:
    """
    封装与 AirSim 的交互，提供简化的接口来控制无人机。
    """

    def __init__(self):
        """
        初始化 AirSim 客户端并进行连接，启用控制权和解锁无人机。
        """
        self.client = airsim.MultirotorClient()  # 创建一个多旋翼无人机的客户端实例
        self.client.confirmConnection()  # 确认与 AirSim 的连接
        self.client.enableApiControl(True)  # 启用 API 控制权限
        self.client.armDisarm(True)  # 解锁无人机

    def takeoff(self):
        """
        控制无人机起飞。
        """
        self.client.takeoffAsync().join()  # 异步起飞并等待起飞完成

    def land(self):
        """
        控制无人机降落。
        """
        self.client.landAsync().join()  # 异步降落并等待降落完成

    def get_drone_position(self):
        """
        获取当前无人机的位置 (x, y, z)。
        """
        pose = self.client.simGetVehiclePose()  # 获取无人机的位姿
        return [pose.position.x_val, pose.position.y_val, pose.position.z_val]  # 返回位置的坐标值

    def fly_to(self, point):
        """
        控制无人机飞到目标点。
        :param point: 目标点的坐标 (x, y, z)
        """
        # 如果目标点的高度大于 0, 则飞行到 -z 的高度，否则使用原始的 z 值
        if point[2] > 0:
            self.client.moveToPositionAsync(point[0], point[1], -point[2], 5).join()  # 飞到指定的目标位置
        else:
            self.client.moveToPositionAsync(point[0], point[1], point[2], 5).join()

    def fly_path(self, points):
        """
        控制无人机沿给定路径飞行。
        :param points: 路径点的列表，每个点是一个三维坐标 (x, y, z)
        """
        airsim_points = []  # 存储转换后的 AirSim 路径点
        for point in points:
            # 如果 z > 0，将 z 值取负，符合 AirSim 飞行规则
            if point[2] > 0:
                airsim_points.append(airsim.Vector3r(point[0], point[1], -point[2]))
            else:
                airsim_points.append(airsim.Vector3r(point[0], point[1], point[2]))
        # 使用 moveOnPathAsync 方法沿路径飞行
        self.client.moveOnPathAsync(
            airsim_points,  # 路径点
            5,  # 每秒最大速度
            120,  # 最大允许飞行时间
            airsim.DrivetrainType.ForwardOnly,  # 仅支持前进的驱动方式
            airsim.YawMode(False, 0),  # 设置偏航角控制模式
            20,  # 路径的最大曲率
            1  # 路径的采样频率
        ).join()

    def set_yaw(self, yaw):
        """
        设置无人机的偏航角（航向角）。
        :param yaw: 目标偏航角，单位为度
        """
        self.client.rotateToYawAsync(yaw, 5).join()  # 异步旋转到指定的偏航角

    def get_yaw(self):
        """
        获取无人机的当前偏航角。
        """
        orientation_quat = self.client.simGetVehiclePose().orientation  # 获取无人机的四元数姿态
        yaw = airsim.to_eularian_angles(orientation_quat)[2]  # 从四元数转化为欧拉角并提取偏航角
        return yaw  # 返回当前偏航角

    def get_position(self, object_name):
        """
        获取指定物体的位置。
        :param object_name: 物体的名称，使用 objects_dict 中的映射
        """
        # 使用物体名称在 Unreal Engine 中进行搜索，匹配所有相关对象
        query_string = objects_dict[object_name] + ".*"
        object_names_ue = []
        while len(object_names_ue) == 0:
            object_names_ue = self.client.simListSceneObjects(query_string)  # 获取场景中匹配的对象列表
        pose = self.client.simGetObjectPose(object_names_ue[0])  # 获取第一个匹配物体的位置
        return [pose.position.x_val, pose.position.y_val, pose.position.z_val]  # 返回物体的位置
