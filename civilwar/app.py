import datetime
import logging
import os
from functools import update_wrapper
from dotenv import load_dotenv

from flask import Flask, session, request, send_from_directory
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO, emit
from utils.api import create_response, create_error

import gamecontroller

load_dotenv()

ORIGINS = ["https://dnd.romanh.de", "https://localhost:3000", "http://localhost:3000"]
gc = gamecontroller.GameController()
app = Flask(__name__)
# app.config.from_object(__name__)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
Session(app)
socketio = SocketIO(app, cors_allowed_origins=ORIGINS, cookie='session', manage_session=False)
cors = CORS(app, origins=ORIGINS)


def has_character():
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            # First check if user is authenticated.
            if session.get("character", None) is None:
                return create_error("No character chosen yet")

            return fn(*args, **kwargs)
        return update_wrapper(wrapped_function, fn)
    return decorator


def has_role(*required_roles):
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            # First check if user is authenticated.
            current_role = session.get("role", None)
            if len(required_roles) > 0 and current_role not in required_roles:
                required_roles = ",".join(required_roles)
                return create_error(f"Insufficient permissions. Roles needed: {required_roles}, role got: {current_role}")

            return fn(*args, **kwargs)
        return update_wrapper(wrapped_function, fn)
    return decorator


def require_params(params):
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            data = args[0]
            for param_name, param_def in params.items():
                if param_name not in data:
                    if not param_def.get("optional", False):
                        return create_error(f"Missing required parameter: {param_name}")
                    else:
                        data[param_name] = param_def.get("default", None)
                elif "type" in param_def:
                    required_type = param_def["type"]
                    value = data[param_name]
                    if not isinstance(value, required_type):
                        return create_error(f"Invalid type for parameter {param_name}, "
                                            f"required: {required_type}, got: {type(value)}")

            return fn(*args, **kwargs)
        return update_wrapper(wrapped_function, fn)
    return decorator


@app.before_request
def before_request_callback():
    # Force setting cookie
    session["role"] = session.get("role", "player")
    session["character"] = session.get("character", None)


@app.route("/")
def index_route():
    return send_from_directory('static', "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory('static', path)


@socketio.on("disconnect")
def on_disconnect():
    character_id = session.get("character", None)
    character = gc.get_character(character_id)
    if character:
        gc.remove_character(character_id)


@socketio.on("connect")
def on_connect():
    character_id = session.get("character", None)
    # TODO: this will always return None, since the character is not longer present in the game controller
    character = gc.get_character(character_id)
    if character:
        emit("characterJoin", create_response(character), broadcast=True)


@socketio.on('chooseCharacter')
@require_params({"name": {"type": str}})
def choose_character(data):
    character_id = session.get("character", None)
    if gc.get_character(character_id) is not None:
        response = create_error("You already chose a character")
    else:
        character = gc.create_pc(data["name"])
        if isinstance(character, dict):  # error
            response = character
        else:
            session["character"] = character.get_id()
            response = create_response(character)
            emit("characterJoin", create_response(data=character), broadcast=True)

    emit("chooseCharacter", response)


@socketio.on('getSelectableCharacters')
def get_selectable_characters(data):
    pc_configs = gc.get_character_configs(lambda c: c["type"] == "player")
    emit("getSelectableCharacters", create_response(data=pc_configs))


@socketio.on("getCharacters")
def get_characters(data):
    response = create_response(data=gc.get_all_characters())
    emit("getCharacters", response)


@socketio.on("getPCs")
def get_playable_characters(data):
    emit("getPCs", create_response(data=gc.get_pcs()))


@socketio.on("getAllies")
def get_allies(data):
    emit("getAllies", create_response(data=gc.get_allies()))


@socketio.on("getEnemies")
def get_enemies(data):
    emit("getEnemies", create_response(data=gc.get_enemies()))


@socketio.on('info')
def api_info(data):

    player = {
        "role": session.get("role", "player"),
    }

    character_id = session.get("character", None)
    character = gc.get_character(character_id)
    player["character"] = character_id
    if character is not None:
        player["character"] = character
    else:
        player["character"] = None

    emit("info", create_response(data={"player": player}))


@socketio.on('attack')
@has_character()
def api_attack(data):
    character = session["character"]
    target = data.get("target", None)
    if target is None:
        emit("attack", create_error("No target selected"))
    else:
        emit("attack", create_response(gc.attack(character, target)), broadcast=True)


@socketio.on('cast')
def api_cast(data):
    pass


# Also for DM
@socketio.on('move')
def api_move(data):
    resp = None
    if "target" not in data.keys() or "pos" not in data.keys() or "real_pixels" not in data.keys():
        resp = {"success": "false", "msg": "Missing keys: target, pos or real_pixels", "data": {}}
    if resp is None:
        resp = gc.move(data["target"], data["pos"], data["real_pixels"])
    emit("move", resp, broadcast=True)


@socketio.on('turn')
def api_pass_turn(data):
    pass


@socketio.on('switchWeapon')
@has_character()
def api_switch_weapon(data):
    resp = None
    character = session["character"]
    weapon_name = data.get("name", None)
    if weapon_name is None:
        resp = create_error("No weapon selected")
    if resp is None:
        resp = gc.switch_weapon(weapon_name, character)
    emit("switchWeapon", resp)


### DM methods
@socketio.on('start')
@has_role("dm")
def dm_start(data):
    return gc.start()


@socketio.on('changeHealth')
@has_role("dm")
def dm_change_health(data):
    resp = None
    character = data.get("character", None)
    if character is None:
        resp = create_error("No character selected")
    life_points = data.get("life", 0)
    if resp is None:
        resp = gc.change_health(character, life_points)
    emit("changeHealth", resp, broadcast=True)


@socketio.on('reset')
@has_role("dm")
def dm_reset(data):
    global gc
    gc = gamecontroller.GameController()
    emit("reset", create_response(), broadcast=True)


@socketio.on('continue')
@has_role("dm")
def dm_continue(data):
    pass


@socketio.on('addTurn')
@has_role("dm")
def dm_add_turn(data):
    pass


@socketio.on('stun')
@has_role("dm")
def dm_stun(data):
    resp = None
    character = data.get("character", None)
    if character is None:
        resp = create_error("No character selected")
    if resp is None:
        resp = gc.stun(character)
    emit("stun", resp, broadcast=True)


@socketio.on('createNPCs')
@has_role("dm")
@require_params({"allies": {"type": bool}, "amount": {"type": int}})
def dm_create_npcs(data):
    resp = gc.create_npc(data["amount"], data["allies"])
    emit("createNPCs", resp, broadcast=True)


if __name__ == "__main__":
    logging.basicConfig(filename='logs/debug.log', level=logging.DEBUG)
    app.run("localhost", 8001)
