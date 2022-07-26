from utils.json_serializable import JsonSerializable


def json_serialize(data):
    if isinstance(data, dict):
        for key in list(data.keys()):
            data[key] = json_serialize(data[key])
    elif isinstance(data, list):
        for i, value in enumerate(data):
            data[i] = json_serialize(value)
    elif isinstance(data, JsonSerializable):
        return data.to_json()

    return data


def create_response(data=None, success=True, msg=""):
    data = {} if data is None else data
    data = json_serialize(data)
    return {"success": success, "msg": msg, "data": data}


def create_error(msg=""):
    return create_response(success=False, msg=msg)
