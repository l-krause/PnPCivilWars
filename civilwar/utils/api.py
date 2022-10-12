from abc import ABC, abstractmethod
from functools import update_wrapper

from flask import session, request
from flask_socketio import emit

from utils.json_serializable import JsonSerializable


def json_serialize(data):
    if isinstance(data, dict):
        data = data.copy()
        for key in list(data.keys()):
            data[key] = json_serialize(data[key])
    elif isinstance(data, list):
        data = data.copy()
        for i, value in enumerate(data):
            data[i] = json_serialize(value)
    elif isinstance(data, JsonSerializable):
        return json_serialize(data.to_json())

    return data


def create_response(data=None, success=True, msg=""):
    data = {} if data is None else data
    return {"success": success, "msg": msg, "data": json_serialize(data)}


def create_error(msg=""):
    return create_response(success=False, msg=msg)


def broadcast_response(response):
    event = request.event["message"]
    emit(event, response)
    if response["success"]:
        emit(event, response["data"], broadcast=True, include_self=False)


def has_character():
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            if session.get("character", None) is None:
                return emit(request.event['message'], create_error("No character chosen yet"))

            return fn(*args, **kwargs)

        return update_wrapper(wrapped_function, fn)

    return decorator


def has_role(*required_roles):
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            # First check if user is authenticated.
            current_role = session.get("role", None)
            if len(required_roles) > 0 and current_role not in required_roles:
                required_roles_str = ",".join(required_roles)
                emit(request.event['message'],
                     create_error(f"Insufficient permissions. "
                                  f"Roles needed: {required_roles_str}, role got: {current_role}"))
                return

            return fn(*args, **kwargs)

        return update_wrapper(wrapped_function, fn)

    return decorator


def param(param_name, required_type=None, optional=False, default=None):
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            data = args[0]
            event = request.event['message']
            if param_name not in data:
                if not optional:
                    emit(event, create_error(f"Missing required parameter: {param_name}"))
                    return
                else:
                    data[param_name] = default
            elif required_type is not None:
                value = data[param_name]
                if issubclass(required_type, ApiParameter):
                    from gamecontroller import GameController
                    res = required_type.api_validate(GameController.instance(), value)
                    if isinstance(res, dict) and res.get("success", None) is False:
                        res["msg"] = f"Error validating parameter '{param_name}': " + res["msg"]
                        emit(event, res)
                        return
                    else:
                        data[param_name] = res
                elif not isinstance(value, required_type):
                    if (required_type == tuple and isinstance(value, list)) or \
                            (required_type == list and isinstance(value, tuple)):
                        pass
                    else:

                        emit(event, create_error(f"Invalid type for parameter {param_name}, "
                                                 f"required: {required_type}, got: {type(value)}"))
                        return

            return fn(*args, **kwargs)

        return update_wrapper(wrapped_function, fn)

    return decorator


class ApiParameter(ABC):
    @staticmethod
    @abstractmethod
    def api_validate(game_controller, value):
        pass
