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
    speed_modifier = args.get("speed_modifier", "normal").lower()
    duration_modifier = args.get("duration_modifier", "normal").lower()
    
    # Base speeds for each direction
    base_speeds = {
        "forward": 0.8,
        "backward": -0.2,
        "left": 0.2,
        "right": -0.2
    }
    
    # Speed modifiers
    speed_multipliers = {
        "slow": 0.3,
        "slowly": 0.3,
        "bit": 0.4,
        "little": 0.4,
        "normal": 1.0,
        "fast": 1.5,
        "quickly": 1.5,
        "lot": 1.5,
        "much": 1.5
    }
    
    # Duration modifiers
    duration_multipliers = {
        "short": 0.3,
        "briefly": 0.3,
        "moment": 0.5,
        "normal": 1.0,
        "long": 3.0,
        "long_time": 3.0,
        "extended": 3.0,
        "while": 2.0
    }
    
    # Apply duration modifier to distance
    final_distance = distance * duration_multipliers.get(duration_modifier, 1.0)
    
    if direction == "stop":
        x, y, z = 0.0, 0.0, 0.0
        speed_multiplier = 1.0
    else:
        base_speed = base_speeds.get(direction, 0.0)
        speed_multiplier = speed_multipliers.get(speed_modifier, 1.0)
        
        if direction == "forward":
            x = base_speed * speed_multiplier
            y, z = 0.0, 0.0
        elif direction == "backward":
            x = base_speed * speed_multiplier
            y, z = 0.0, 0.0
        elif direction == "left":
            x, y, z = 0.0, base_speed * speed_multiplier, 0.0
        elif direction == "right":
            x, y, z = 0.0, base_speed * speed_multiplier, 0.0
        else:
            return {
                "error": f"Invalid direction: {direction}",
                "message": f"Unknown direction: {direction}"
            }
    
    res = _robot_client.Move(x, y, z)
    time.sleep(final_distance)
    _robot_client.Move(0.0, 0.0, 0.0)
    
    return {
        "direction": direction,
        "speed_modifier": speed_modifier,
        "duration_modifier": duration_modifier,
        "actual_speed": abs(x) if x != 0 else abs(y),
        "final_duration": final_distance,
        "status": "success" if res == 0 else "failed",
        "message": f"Robot moved {direction} {speed_modifier} for {final_distance:.1f}s"
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
        "description": "Move the robot in a direction with speed control (forward, backward, left, right, stop)",
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
                },
                "speed_modifier": {
                    "type": "string",
                    "enum": ["slow", "slowly", "bit", "little", "normal", "fast", "quickly", "lot", "much"],
                    "description": "Speed modifier: 'slow/slowly/bit/little' for gentle movement, 'normal' for standard speed, 'fast/quickly/lot/much' for faster movement"
                },
                "duration_modifier": {
                    "type": "string",
                    "enum": ["short", "briefly", "moment", "normal", "long", "long_time", "extended", "while"],
                    "description": "Duration modifier: 'short/briefly/moment' for quick movements, 'normal' for standard duration, 'long/long_time/extended/while' for longer movements"
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

