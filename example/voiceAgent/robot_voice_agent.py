import sys
import asyncio
import os
import time
import random
sys.path.insert(0, '../..')
from booster_robotics_sdk_python import B1LocoClient, ChannelFactory, RobotMode, B1HandIndex, Position, Orientation, Posture, DexterousFingerParameter, GripperMotionParameter, GripperControlMode, Frame, Transform, GetModeResponse
from dotenv import load_dotenv
from agent import VoiceAgent
from robot_tools import ROBOT_TOOLS_REGISTRY, ROBOT_TOOLS_DEFINITIONS, set_robot_client

def hand_rock(client: B1LocoClient):
    finger_params = []
    for i in range(6):
        finger_param = DexterousFingerParameter()
        finger_param.seq = 5 if i == 5 else i
        finger_param.angle = 0
        finger_param.force = 200
        finger_param.speed = 800
        finger_params.append(finger_param)
    client.ControlDexterousHand(finger_params, B1HandIndex.kRightHand)

def hand_scissor(client: B1LocoClient):
    angles = [0, 0, 1000, 1000, 0, 0]
    finger_params = []
    for i, angle in enumerate(angles):
        finger_param = DexterousFingerParameter()
        finger_param.seq = 5 if i == 5 else i
        finger_param.angle = angle
        finger_param.force = 200
        finger_param.speed = 800
        finger_params.append(finger_param)
    client.ControlDexterousHand(finger_params, B1HandIndex.kRightHand)

def hand_paper(client: B1LocoClient):
    finger_params = []
    for i in range(6):
        finger_param = DexterousFingerParameter()
        finger_param.seq = 5 if i == 5 else i
        finger_param.angle = 1000
        finger_param.force = 200
        finger_param.speed = 800
        finger_params.append(finger_param)
    client.ControlDexterousHand(finger_params, B1HandIndex.kRightHand)

def hand_ok(client: B1LocoClient):
    angles = [1000, 1000, 1000, 500, 400, 350]
    finger_params = []
    for i, angle in enumerate(angles):
        finger_param = DexterousFingerParameter()
        finger_param.seq = 5 if i == 5 else i
        finger_param.angle = angle
        finger_param.force = 200
        finger_param.speed = 800
        finger_params.append(finger_param)
    client.ControlDexterousHand(finger_params, B1HandIndex.kRightHand)

def celebration_sequence(client: B1LocoClient):
    left_posture = Posture()
    left_posture.position = Position(0.3, 0.3, 0.4)
    left_posture.orientation = Orientation(0.0, 0.0, 0.0)
    client.MoveHandEndEffector(left_posture, 1000, B1HandIndex.kLeftHand)
    
    right_posture = Posture()
    right_posture.position = Position(0.3, -0.3, 0.4)
    right_posture.orientation = Orientation(0.0, 0.0, 0.0)
    client.MoveHandEndEffector(right_posture, 1000, B1HandIndex.kRightHand)
    
    time.sleep(1.0)
    client.Move(0.8, 0.0, 0.0)
    time.sleep(1.0)
    client.Move(0.0, 0.0, 0.0)

async def keyboard_control_loop(client: B1LocoClient):
    x, y, z, yaw, pitch = 0.0, 0.0, 0.0, 0.0, 0.0
    
    while True:
        await asyncio.sleep(0.01)
        input_cmd = await asyncio.to_thread(input)
        input_cmd = input_cmd.strip()
        
        if not input_cmd:
            continue
            
        need_print = False
        res = 0
        
        if input_cmd == "mp":
            res = client.ChangeMode(RobotMode.kPrepare)
        elif input_cmd == "cel":
            celebration_sequence(client)
        elif input_cmd == "md":
            res = client.ChangeMode(RobotMode.kDamping)
        elif input_cmd == "mw":
            res = client.ChangeMode(RobotMode.kWalking)
        elif input_cmd == 'mc':
            res = client.ChangeMode(RobotMode.kCustom)
        elif input_cmd == "stop":
            x, y, z = 0.0, 0.0, 0.0
            need_print = True
            res = client.Move(x, y, z)
        elif input_cmd == "w":
            x, y, z = 0.8, 0.0, 0.0
            need_print = True
            res = client.Move(x, y, z)
        elif input_cmd == "a":
            x, y, z = 0.0, 0.2, 0.0
            need_print = True
            res = client.Move(x, y, z)
        elif input_cmd == "s":
            x, y, z = -0.2, 0.0, 0.0
            need_print = True
            res = client.Move(x, y, z)
        elif input_cmd == "d":
            x, y, z = 0.0, -0.2, 0.0
            need_print = True
            res = client.Move(x, y, z)
        elif input_cmd == "q":
            x, y, z = 0.0, 0.0, 0.2
            need_print = True
            res = client.Move(x, y, z)
        elif input_cmd == "e":
            x, y, z = 0.0, 0.0, -0.2
            need_print = True
            res = client.Move(x, y, z)
        elif input_cmd == "hd":
            yaw, pitch = 0.0, 1.0
            need_print = True
            res = client.RotateHead(pitch, yaw)
        elif input_cmd == "hu":
            yaw, pitch = 0.0, -0.3
            need_print = True
            res = client.RotateHead(pitch, yaw)
        elif input_cmd == "hr":
            yaw, pitch = -0.785, 0.0
            need_print = True
            res = client.RotateHead(pitch, yaw)
        elif input_cmd == "hl":
            yaw, pitch = 0.785, 0.0
            need_print = True
            res = client.RotateHead(pitch, yaw)
        elif input_cmd == "ho":
            yaw, pitch = 0.0, 0.0
            need_print = True
            res = client.RotateHead(pitch, yaw)
        elif input_cmd == "hand-down":
            tar_posture = Posture()
            tar_posture.position = Position(0.28, -0.25, 0.05)
            tar_posture.orientation = Orientation(0.0, 0.0, 0.0)
            res = client.MoveHandEndEffector(tar_posture, 1000, B1HandIndex.kRightHand)
            time.sleep(0.3)
            r_num = random.randint(0, 2)
            if r_num == 0:
                hand_rock(client)
            elif r_num == 1:
                hand_scissor(client)
            else:
                hand_paper(client)
        elif input_cmd == "hand-up":
            tar_posture = Posture()
            tar_posture.position = Position(0.25, -0.3, 0.25)
            tar_posture.orientation = Orientation(0.0, -1.0, 0.0)
            res = client.MoveHandEndEffector(tar_posture, 1000, B1HandIndex.kRightHand)
            time.sleep(0.3)
            hand_paper(client)
        elif input_cmd == "paper":
            hand_paper(client)
        elif input_cmd == "scissor":
            hand_scissor(client)
        elif input_cmd == "rock":
            hand_rock(client)
        elif input_cmd == "ok":
            hand_ok(client)
        elif input_cmd == "quit" or input_cmd == "exit":
            print("Exiting...")
            break
        
        if need_print:
            print(f"Param: {x} {y} {z}")
            print(f"Head param: {pitch} {yaw}")
        
        if res != 0:
            print(f"Request failed: error = {res}")

async def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} networkInterface")
        sys.exit(-1)
    
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    print("🤖 Initializing robot...")
    ChannelFactory.Instance().Init(0, sys.argv[1])
    
    robot_client = B1LocoClient()
    robot_client.Init()
    
    set_robot_client(robot_client)
    
    robot_client.ChangeMode(RobotMode.kWalking)
    print("✓ Robot initialized in walking mode")
    
    print("\n" + "="*60)
    print("DUAL CONTROL MODE")
    print("="*60)
    print("🎤 VOICE CONTROL: Just speak naturally to control the robot")
    print("⌨️  KEYBOARD CONTROL: Use commands like 'w', 's', 'a', 'd', etc.")
    print("="*60 + "\n")
    
    print("🎤 Starting voice agent...")
    agent = VoiceAgent(
        api_key=api_key,
        extra_tools_registry=ROBOT_TOOLS_REGISTRY,
        extra_tools_definitions=ROBOT_TOOLS_DEFINITIONS
    )
    
    try:
        voice_task = asyncio.create_task(agent.run())
        keyboard_task = asyncio.create_task(keyboard_control_loop(robot_client))
        
        await asyncio.gather(voice_task, keyboard_task, return_exceptions=True)
        
    except KeyboardInterrupt:
        print("\n⏹  Stopping...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        robot_client.Move(0.0, 0.0, 0.0)
        await agent.cleanup()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
