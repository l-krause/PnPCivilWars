import datetime
import logging
import os

from dotenv import load_dotenv
from flask import Flask, session, send_from_directory
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO, emit

from gamecontroller import GameController
from utils.api import create_response, create_error, json_serialize, param, has_role, has_character, broadcast_response, \
    emit_character_update
from utils.characters.character import Character
from utils.position import Position

load_dotenv()

ORIGINS = ["https://dnd.romanh.de", "https://localhost:3000", "http://localhost:3000"]

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
def on_disconnect(*args):
    character_id = session.get("character", None)
    character = GameController.instance().get_character(character_id)
    if character:
        # GAME_CONTROLLER.remove_character(character_id)
        character.is_online = False


@socketio.on("connect")
def on_connect(*args):
    character_id = session.get("character", None)
    character = GameController.instance().get_character(character_id)
    if character:
        character.is_online = True
#        emit("characterJoin", json_serialize(character), broadcast=True)


@socketio.on('chooseCharacter')
@param("name", required_type=str)
def choose_character(data):
    logging.debug("socketIO chooseCharacter")
    character_id = session.get("character", None)
    game_controller = GameController.instance()

    if game_controller.get_character(character_id) is not None:
        response = create_error("You already chose a character")
    else:
        character = game_controller.create_pc(data["name"])
        if isinstance(character, dict):  # error
            response = character
        else:
            session["character"] = character.get_id()
            response = create_response(character)
            emit("characterJoin", json_serialize(character), broadcast=True)

    emit("chooseCharacter", response)


@socketio.on('getSelectableCharacters')
def get_selectable_characters(data):
    pc_configs = GameController.instance().get_character_configs(lambda c: c["type"] == "player")
    emit("getSelectableCharacters", create_response(data=pc_configs))


@socketio.on("getCharacters")
def get_characters(data):
    response = create_response(data=GameController.instance().get_all_characters())
    emit("getCharacters", response)


@socketio.on("getPCs")
def get_playable_characters(data):
    emit("getPCs", create_response(data=GameController.instance().get_player_characters()))


@socketio.on("getAllies")
def get_allies(data):
    emit("getAllies", create_response(data=GameController.instance().get_allies()))


@socketio.on("getEnemies")
def get_enemies(data):
    emit("getEnemies", create_response(data=GameController.instance().get_enemies()))


@socketio.on('info')
def api_info(data):
    player = {
        "role": session.get("role", "player"),
    }

    character_id = session.get("character", None)
    character = GameController.instance().get_character(character_id)
    player["character"] = character_id
    if character is not None:
        player["character"] = character
    else:
        player["character"] = None

    emit("info", create_response(data={"player": player}))


@socketio.on('attack')
@has_character()
@param("target", required_type=Character)
def api_attack(data):
    game_controller = GameController.instance()
    character = game_controller.get_character(session["character"])
    response = game_controller.attack(character, data["target"])
    broadcast_response(response)


@socketio.on('cast')
def api_cast(data):
    pass


@socketio.on('move')
@param("target", required_type=Character, optional=True)
@param("pos", required_type=Position)
def api_move(data):
    game_controller = GameController.instance()
    target = data.get("target", None)
    own_character = session.get("character", None)

    if target is None:
        if own_character is None:
            emit("move", create_error("No character given or chosen yet"))
            return
        else:
            target = own_character
    elif session.get("role", "player") != "dm" and (own_character is None or own_character != target):
        emit("move", create_error("Insufficient permissions to move other characters"))
        return

    response = game_controller.move(target, data["pos"])
    emit_character_update(response, data["target"])


@socketio.on('pass')
def api_pass_turn(data):
    broadcast_response(GameController.instance().next_turn())


@socketio.on('switchWeapon')
@has_character()
def api_switch_weapon(data):
    resp = None
    character = session["character"]
    weapon_name = data.get("name", None)
    if weapon_name is None:
        resp = create_error("No weapon selected")
    if resp is None:
        resp = GameController.instance().switch_weapon(weapon_name, character)
    emit("switchWeapon", resp)


@socketio.on("login")
@param("password", required_type=str)
def login(data):
    if data["password"] == "123":
        session["role"] = "dm"
        emit("login", create_response())
    else:
        emit("login", create_error("Wrong Password"))


### DM methods
@socketio.on('start')
@has_role("dm")
def dm_start(data):
    broadcast_response(GameController.instance().start())


@socketio.on('changeHealth')
@has_role("dm")
@param("target", required_type=Character)
@param("life", required_type=int, default=0, optional=True)
def dm_change_health(data):
    game_controller = GameController.instance()
    life_points = data["life"]
    response = game_controller.change_health(data["target"], life_points)
    emit_character_update(response, data["target"])


@socketio.on('reset')
@has_role("dm")
def dm_reset(data):
    GameController.reset()
    emit("reset", {}, broadcast=True)


@socketio.on('continue')
@has_role("dm")
def dm_continue(data):
    resp = GameController.instance().next_turn()
    broadcast_response(resp)


@socketio.on("place")
@has_role("dm")
@param("target", required_type=Character)
@param("pos", required_type=Position)
def place(data):
    game_controller = GameController.instance()
    response = game_controller.place(data["target"], data["pos"])
    emit_character_update(response, data["target"])


@socketio.on('addTurn')
@has_role("dm")
@param("target", required_type=Character)
def dm_add_turn(data):
    resp = GameController.instance().add_turn(data["target"])
    emit("addTurn", resp)


@socketio.on('stun')
@has_role("dm")
@param("target", required_type=Character)
def dm_stun(data):
    resp = GameController.instance().stun(data["target"])
    emit_character_update(resp, data["target"])


@socketio.on('createNPCs')
@has_role("dm")
@param("allies", required_type=bool)
@param("amount", required_type=int)
def dm_create_npcs(data):
    response = GameController.instance().create_npc(data["amount"], data["allies"])
    emit("createNPCs", response, broadcast=True)


if __name__ == "__main__":
    logging.basicConfig(filename='logs/debug.log', level=logging.DEBUG)
    app.run("localhost", 8001)
