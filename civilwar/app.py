import datetime
import logging
import os

from dotenv import load_dotenv
from flask import Flask, session, send_from_directory, request
from flask_cors import CORS
from flask_session import Session
from flask_socketio import SocketIO, emit

from gamecontroller import GameController
from utils.api import create_response, create_error, param, has_role, has_character, broadcast_response
from utils.character_stats import CharacterStats
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
app.config["SESSION_USE_SIGNER"] = True
app.config['SECRET_KEY'] = os.urandom(32)
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
        character.remove_client_sid(request.sid)


@socketio.on("connect")
def on_connect(*args):
    character_id = session.get("character", None)
    character = GameController.instance().get_character(character_id)
    if character:
        character.add_client_sid(request.sid)


#        emit("characterJoin", json_serialize(character), broadcast=True)


@socketio.on('chooseCharacter')
@param("name", required_type=str)
@param("password", required_type=str, optional=True)
def choose_character(data):
    logging.debug("socketIO chooseCharacter")
    character_id = session.get("character", None)
    game_controller = GameController.instance()

    if game_controller.get_character(character_id) is not None:
        response = create_error("You already chose a character")
    else:
        if data["name"].lower() == "crab":
            password = data.get("password", None)
            if password != os.getenv("DM_PASSWORD"):
                emit("login", create_error("Wrong Password"))
                return
            role = "dm"
        else:
            role = "player"

        character = game_controller.create_pc(data["name"])
        if isinstance(character, dict):  # error
            response = character
        else:
            character.add_client_sid(request.sid)
            session["character"] = character.get_id()
            session["role"] = role
            response = create_response({"character": character, "role": role})
            game_controller.send_game_event("characterJoin", {"character": character})

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
    emit("attack", response)


@socketio.on('cast')
def api_cast(data):
    pass


@socketio.on('move')
@param("target", required_type=Character, optional=True)
@param("pos", required_type=Position)
def api_move(data):
    game_controller = GameController.instance()
    target = data.get("target", None)
    own_character = game_controller.get_character(session.get("character", None))

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
    emit("move", response)


@socketio.on('dash')
@has_character()
def dash(data):
    game_controller = GameController.instance()
    character_id = session.get("character")
    target = game_controller.get_character(character_id)
    response = game_controller.dash(target)
    emit("dash", response)


@socketio.on('pass')
@has_character()
def api_pass_turn(data):
    game_controller = GameController.instance()
    character = game_controller.get_character(session["character"])
    if game_controller.get_turn().get_active() != character:
        response = create_error("It's not your turn")
    else:
        response = game_controller.next_turn()
    emit("pass", response)


@socketio.on('switchWeapon')
@param("name", required_type=str)
@has_character()
def api_switch_weapon(data):
    game_controller = GameController.instance()
    character = game_controller.get_character(session["character"])
    if character._stunned > 0:
        emit("characterStunned", create_error("You are stunned"))
        return
    weapon = character.get_weapon(data["name"])
    if not weapon:
        resp = create_error("You do not own such weapon")
    else:
        resp = character.switch_weapon(weapon)

    emit("switchWeapon", resp)


### DM methods
@socketio.on('start')
@has_role("dm")
def dm_start(data):
    GameController.instance().start()
    return create_response()


@socketio.on('changeHealth')
@has_role("dm")
@param("target", required_type=int)
@param("life", required_type=int, default=0, optional=True)
def dm_change_health(data):
    game_controller = GameController.instance()
    character = game_controller.get_character(data["target"])
    if character is None:
        emit("changeHealth", create_error("Character does not exist"))
        return
    character.change_health(data["life"])
    character.send_character_event("characterChangedHp", {"hp": data["life"]})
    emit('changeHealth', create_response())


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
    response = data["target"].place(data["pos"])
    emit("place", response)


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
    response = data["target"].stun(1)
    emit("stun", response)


@socketio.on('createNPCs')
@has_role("dm")
@param("allies", required_type=bool)
@param("amount", required_type=int)
def dm_create_npcs(data):
    game_controller = GameController.instance()
    response = game_controller.create_npcs(data["amount"], data["allies"])
    emit("createNPCs", response)


@socketio.on("kill")
@has_role("dm")
@param("target", required_type=Character)
def dm_kill(data):
    data["target"].kill(reason="DM kill")


@socketio.on('changeSelChar')
@has_role("dm")
@param("character", required_type=Character)
@param("stats", required_type=CharacterStats)
def dm_change_char(data):
    target = data["character"]
    if target.is_transformed():
        target.retransform()
    else:
        target.transform(data["stats"])

    emit("changeSelChar", create_response())


if __name__ == "__main__":
    log_file = 'logs/debug.log'
    log_dir = os.path.dirname(log_file)

    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(filename=log_file, level=logging.DEBUG)
    app.run("localhost", 8001)
