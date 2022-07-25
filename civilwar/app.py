from functools import update_wrapper

from flask import Flask, send_from_directory, Response, session
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO, emit

import gamecontroller

CHARACTERS = ["configs/manollo.json", "configs/thork.json", "configs/martha.json", "configs/bart.json"]
ORIGINS = ["https://dnd.romanh.de", "https://localhost:3000", "http://localhost:3000"]
gc = gamecontroller.GameController()
app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
socketio = SocketIO(app, cors_allowed_origins=ORIGINS)
cors = CORS(app, origins=ORIGINS)
Session(app)


def create_error(msg=""):
    return {"success": False, "msg": msg}


def has_character():
    def decorator(fn):
        def wrapped_function(*args, **kwargs):
            # First check if user is authenticated.
            if session.get("character", None) is None:
                return {"success": False, "msg": "No character chosen yet"}

            return fn(*args, **kwargs)

        return update_wrapper(wrapped_function, fn)

    return decorator


@app.route('/test')
def test_route():
    return Response("test")


@app.route('/')
def index():
    return send_from_directory('static', "index.html")


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@socketio.on('chooseCharacter')
def choose_character(data):
    if session.get("character", None) is not None:
        response = create_error("You already chose a character")
    else:
        index = int(data["characterIndex"])
        if 0 > index or index > len(CHARACTERS):
            response = create_error(f"Invalid character: {index}")
        else:
            session["character"] = index
            response = gc.create_pc(CHARACTERS[index])

    emit("chooseCharacter", response)


@socketio.on("getCharacters")
def get_characters(data):
    response = gc.get_all_characters()
    emit("getCharacter", response)


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
    return gc.attack(data["character"]["name"], data["target"]["name"])


@socketio.on('cast')
def api_cast(data):
    pass


@socketio.on('move')
def api_move(data):
    if "target" not in data.keys() or "pos" not in data.keys() or "real_pixels" not in data.keys():
        return {"success": "false", "msg": "Missing keys: target, pos or real_pixels", "data": {}}
    gc.move(data["target"], data["pos"], data["real_pixels"])


@socketio.on('turn')
def api_pass_turn(data):
    pass


@socketio.on('switchWeapon')
def api_switch_weapon(data):
    pass


### DM methods
@socketio.on('start')
def dm_start(data):
    return gc.start()


@socketio.on('changeHealth')
def dm_change_health(data):
    pass


@socketio.on('reset')
def dm_reset(data):
    pass


@socketio.on('continue')
def dm_continue(data):
    pass


@socketio.on('createNPCs')
def dm_create_npcs(data):
    if not ("allies" in data.keys() and "amount" in data.keys()):
        return {"success": False, "msg": "Missing keys: allies or amount", "data": {}}
    return gc.create_npc(data["amount"], data["allies"])


if __name__ == "__main__":
    app.run("localhost", 8001)
