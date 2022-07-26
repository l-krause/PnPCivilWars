from functools import update_wrapper

from flask import Flask, session
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO, emit
from utils.api import create_response, create_error

import gamecontroller

ORIGINS = ["https://dnd.romanh.de", "https://localhost:3000", "http://localhost:3000"]
gc = gamecontroller.GameController()
app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
socketio = SocketIO(app, cors_allowed_origins=ORIGINS)
cors = CORS(app, origins=ORIGINS)
Session(app)


def has_character():
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            # First check if user is authenticated.
            if session.get("character", None) is None:
                return {"success": False, "msg": "No character chosen yet"}

            return fn(*args, **kwargs)

        return update_wrapper(wrapped_function, fn)

    return decorator


@socketio.on('chooseCharacter')
def choose_character(data):
    if session.get("character", None) is not None:
        response = create_error("You already chose a character")
    else:
        playable_characters = gc.get_pcs()
        character_name = data.get("name", None)
        if character_name is None:
            response = create_error("You have to specify the character's name you want to play")
        elif character_name not in playable_characters:
            response = create_error(f"Invalid character: {character_name}")
        else:
            session["character"] = playable_characters[character_name]
            response = create_response()

    emit("chooseCharacter", response)


@socketio.on("getCharacters")
def get_characters(data):
    response = gc.get_all_characters()
    emit("getCharacter", response)


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
def api_info(*args):
    print("INFO received", args)
    player = {
        "role": session.get("role", "player"),
        "character": session.get("character", None),
        "name": session.get("name", "Unnamed Player")
    }

    emit("info", {"success": True, "msg": "", "data": {"player": player}})


@socketio.on('attack')
def api_attack(data):
    resp = None
    character = data.get("character", None)
    if character is None:
        resp = create_error("No character selected")
    target = data.get("target", None)
    if character is None:
        resp = create_error("No target selected")
    if resp is None:
        resp = gc.attack(character, target)
    emit("attack", resp, broadcast=True)


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
def api_switch_weapon(data):
    resp = None
    character = data.get("character", None)
    weapon_name = data.get("name", None)
    if weapon_name is None:
        resp = create_error("No weapon selected")
    if character is None:
        resp = create_error("No character selected")
    if resp is None:
        resp = gc.switch_weapon(name, character)
    emit("switchWeapon", resp)


### DM methods
@socketio.on('start')
def dm_start(data):
    return gc.start()


@socketio.on('changeHealth')
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
def dm_reset(data):
    gc = gamecontroller.GameController()
    emit("reset", create_response(), broadcast=True)


@socketio.on('continue')
def dm_continue(data):
    pass


@socketio.on('addTurn')
def dm_add_turn(data):
    pass


@socketio.on('stun')
def dm_stun(data):
    resp = None
    character = data.get("character", None)
    if character is None:
        resp = create_error("No character selected")
    if resp is None:
        resp = gc.stun(character)
    emit("stun", resp, broadcast=True)


@socketio.on('createNPCs')
def dm_create_npcs(data):
    resp = None
    if not ("allies" in data.keys() and "amount" in data.keys()):
        resp = {"success": False, "msg": "Missing keys: allies or amount", "data": {}}
    if resp is None:
        resp = gc.create_npc(data["amount"], data["allies"])
    emit("createNPCs". resp, broadcast=True)


if __name__ == "__main__":
    app.run("localhost", 8001)
