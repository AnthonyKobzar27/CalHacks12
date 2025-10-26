import sys
import time
from typing import Dict, Any
sys.path.insert(0, '../..')
from booster_robotics_sdk_python import B1LocoClient, RobotMode, B1HandIndex, B1HandAction, Position, Orientation, Posture, DexterousFingerParameter

_robot_client = None

def set_robot_client(client: B1LocoClient):
    global _robot_client
    _robot_client = client

def move_robot(args: Dict[str, Any]) -> Dict[str, Any]:
    direction = args.get("direction", "forward").lower()
    distance = args.get("distance", 1.0)
    
    x, y, z = 0.0, 0.0, 0.0
    
    if direction == "forward":
        x = 0.8
    elif direction == "backward":
        x = -0.2
    elif direction == "left":
        y = 0.2
    elif direction == "right":
        y = -0.2
    elif direction == "stop":
        x, y, z = 0.0, 0.0, 0.0
    
    res = _robot_client.Move(x, y, z)
    time.sleep(distance)
    _robot_client.Move(0.0, 0.0, 0.0)
    
    return {
        "direction": direction,
        "status": "success" if res == 0 else "failed",
        "message": f"Robot moved {direction}"
    }

def rotate_head(args: Dict[str, Any]) -> Dict[str, Any]:
    direction = args.get("direction", "center").lower()
    
    yaw, pitch = 0.0, 0.0
    
    if direction == "left":
        yaw = 0.785
    elif direction == "right":
        yaw = -0.785
    elif direction == "up":
        pitch = -0.3
    elif direction == "down":
        pitch = 1.0
    elif direction == "center":
        yaw, pitch = 0.0, 0.0
    
    res = _robot_client.RotateHead(pitch, yaw)
    
    return {
        "direction": direction,
        "status": "success" if res == 0 else "failed",
        "message": f"Robot head rotated {direction}"
    }

def celebration(args: Dict[str, Any]) -> Dict[str, Any]:
    left_posture = Posture()
    left_posture.position = Position(0.3, 0.3, 0.4)
    left_posture.orientation = Orientation(0.0, 0.0, 0.0)
    _robot_client.MoveHandEndEffector(left_posture, 1000, B1HandIndex.kLeftHand)
    
    right_posture = Posture()
    right_posture.position = Position(0.3, -0.3, 0.4)
    right_posture.orientation = Orientation(0.0, 0.0, 0.0)
    _robot_client.MoveHandEndEffector(right_posture, 1000, B1HandIndex.kRightHand)
    
    time.sleep(1.0)
    _robot_client.Move(0.8, 0.0, 0.0)
    time.sleep(1.0)
    _robot_client.Move(0.0, 0.0, 0.0)
    
    return {
        "status": "success",
        "message": "Celebration sequence complete!"
    }

def hand_gesture(args: Dict[str, Any]) -> Dict[str, Any]:
    gesture = args.get("gesture", "paper").lower()
    
    finger_params = []
    
    if gesture == "rock":
        angles = [0, 0, 0, 0, 0, 0]
    elif gesture == "scissor":
        angles = [0, 0, 1000, 1000, 0, 0]
    elif gesture == "paper":
        angles = [1000, 1000, 1000, 1000, 1000, 1000]
    elif gesture == "ok":
        angles = [1000, 1000, 1000, 500, 400, 350]
    else:
        angles = [1000, 1000, 1000, 1000, 1000, 1000]
    
    for i, angle in enumerate(angles):
        finger_param = DexterousFingerParameter()
        finger_param.seq = i if i != 5 else 5
        finger_param.angle = angle
        finger_param.force = 200
        finger_param.speed = 800
        finger_params.append(finger_param)
    
    res = _robot_client.ControlDexterousHand(finger_params, B1HandIndex.kRightHand)
    
    return {
        "gesture": gesture,
        "status": "success" if res == 0 else "failed",
        "message": f"Hand gesture {gesture} performed"
    }

def wave_hand(args: Dict[str, Any]) -> Dict[str, Any]:
    action = args.get("action", "open").lower()
    
    if action == "open":
        hand_action = B1HandAction.kHandOpen
    elif action == "close":
        hand_action = B1HandAction.kHandClose
    else:
        return {
            "error": "Invalid action. Must be 'open' or 'close'",
            "message": f"Unknown wave action: {action}"
        }
    
    res = _robot_client.WaveHand(hand_action)
    
    return {
        "action": action,
        "status": "success" if res == 0 else "failed",
        "message": f"Robot waved hand ({action})"
    }

def change_mode(args: Dict[str, Any]) -> Dict[str, Any]:
    mode = args.get("mode", "walking").lower()
    
    mode_map = {
        "walking": RobotMode.kWalking,
        "damping": RobotMode.kDamping,
        "prepare": RobotMode.kPrepare,
        "custom": RobotMode.kCustom
    }
    
    robot_mode = mode_map.get(mode, RobotMode.kWalking)
    res = _robot_client.ChangeMode(robot_mode)
    
    return {
        "mode": mode,
        "status": "success" if res == 0 else "failed",
        "message": f"Robot mode changed to {mode}"
    }

ROBOT_TOOLS_REGISTRY = {
    "move_robot": move_robot,
    "rotate_head": rotate_head,
    "celebration": celebration,
    "hand_gesture": hand_gesture,
    "wave_hand": wave_hand,
    "change_mode": change_mode,
}

ROBOT_TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "name": "move_robot",
        "description": "Move the robot in a direction (forward, backward, left, right, stop)",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["forward", "backward", "left", "right", "stop"],
                    "description": "Direction to move"
                },
                "distance": {
                    "type": "number",
                    "description": "Duration in seconds to move (default 1.0)"
                }
            },
            "required": ["direction"]
        }
    },
    {
        "type": "function",
        "name": "rotate_head",
        "description": "Rotate the robot's head (left, right, up, down, center)",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["left", "right", "up", "down", "center"],
                    "description": "Direction to rotate head"
                }
            },
            "required": ["direction"]
        }
    },
    {
        "type": "function",
        "name": "celebration",
        "description": "Perform a celebration sequence - raise arms and move forward",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "hand_gesture",
        "description": "Make a hand gesture (rock, paper, scissors, ok)",
        "parameters": {
            "type": "object",
            "properties": {
                "gesture": {
                    "type": "string",
                    "enum": ["rock", "paper", "scissor", "ok"],
                    "description": "Which hand gesture to make"
                }
            },
            "required": ["gesture"]
        }
    },
    {
        "type": "function",
        "name": "wave_hand",
        "description": "Wave the robot's hand (open or close)",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["open", "close"],
                    "description": "Hand wave action - 'open' to wave open hand, 'close' to wave closed hand"
                }
            },
            "required": ["action"]
        }
    },
    {
        "type": "function",
        "name": "change_mode",
        "description": "Change robot mode (walking, damping, prepare, custom)",
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["walking", "damping", "prepare", "custom"],
                    "description": "Robot mode to switch to"
                }
            },
            "required": ["mode"]
        }
    }
]

