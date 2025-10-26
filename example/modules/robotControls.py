from booster_robotics_sdk_python import B1LocoClient, ChannelFactory, RobotMode, B1HandIndex, GripperControlMode, Position, Orientation, Posture, GripperMotionParameter, GetModeResponse, Quaternion, Frame, Transform, DexterousFingerParameter
import sys, time, random

#Brotha

def hand_rock(client: B1LocoClient):
    # 定义一个 名为 finger_params 的数组，用于存储每个手指的参数
    finger_params = []
    # 设置每个手指的参数
    finger0_param = DexterousFingerParameter()
    finger0_param.seq = 0
    finger0_param.angle = 0
    finger0_param.force = 200
    finger0_param.speed = 800
    finger_params.append(finger0_param)

    finger1_param = DexterousFingerParameter()
    finger1_param.seq = 1
    finger1_param.angle = 0
    finger1_param.force = 200
    finger1_param.speed = 800
    finger_params.append(finger1_param)

    finger2_param = DexterousFingerParameter()
    finger2_param.seq = 2
    finger2_param.angle = 0
    finger2_param.force = 200
    finger2_param.speed = 800
    finger_params.append(finger2_param)

    finger3_param = DexterousFingerParameter()
    finger3_param.seq = 3
    finger3_param.angle = 0
    finger3_param.force = 200
    finger3_param.speed = 800
    finger_params.append(finger3_param)

    finger4_param = DexterousFingerParameter()
    finger4_param.seq = 3
    finger4_param.angle = 0
    finger4_param.force = 200
    finger4_param.speed = 800
    finger_params.append(finger4_param)

    res = client.ControlDexterousHand(finger_params, B1HandIndex.kRightHand)
    if res != 0:
        print(f"Rock hand failed: error = {res}")

    time.sleep(0.2)

    finger5_param = DexterousFingerParameter()
    finger5_param.seq = 5
    finger5_param.angle = 0
    finger5_param.force = 200
    finger5_param.speed = 800
    finger_params.append(finger5_param)

    res = client.ControlDexterousHand(finger_params, B1HandIndex.kRightHand)
    if res != 0:
        print(f"Rock hand thumb failed: error = {res}")

def raise_arms_celebration(client: B1LocoClient):
    """Raises both arms in a celebration gesture"""

    left_posture = Posture()
    left_posture.position = Position(0.3, 0.3, 0.4)
    left_posture.orientation = Orientation(0.0, 0.0, 0.0)
    res_left = client.MoveHandEndEffector(left_posture, 1000, B1HandIndex.kLeftHand)
    
    right_posture = Posture()
    right_posture.position = Position(0.3, -0.3, 0.4)
    right_posture.orientation = Orientation(0.0, 0.0, 0.0)
    res_right = client.MoveHandEndEffector(right_posture, 1000, B1HandIndex.kRightHand)
    
    if res_left != 0:
        print(f"Left arm raise failed: error = {res_left}")
    if res_right != 0:
        print(f"Right arm raise failed: error = {res_right}")
    
    return res_left if res_left != 0 else res_right

def celebration_sequence(client: B1LocoClient):
    """Complete sequence: raise arms -> move forward 1 second -> stop"""

    print("Vamos")
    
    res = raise_arms_celebration(client)
    time.sleep(1.0)
    res = client.Move(0.8, 0.0, 0.0)
    time.sleep(1.0)

    res = client.Move(0.0, 0.0, 0.0)  # Stop

    print("Sequence completed successfully!")
    return 0