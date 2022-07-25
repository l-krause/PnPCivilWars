import json
import re

import websocket_server

import gamecontroller

CHARACTERS = ["configs/manollo.json", "configs/thork.json", "configs/martha.json", "configs/bart.json"]
gc = gamecontroller.GameController()


def new_client(client, server):
    print("New client connected and was given id %d" % client['id'])


def client_left(client, server):
    print("Client(%d) disconnected" % client['id'])


def message_received(client, server: websocket_server.WebsocketServer, message):
    message = json.loads(message)
    data = message["params"]
    resp = {"success": False, "msg": "Invalid message", "data": {}}
    action = message["action"]
    player_func = "api_" + re.sub(r'(?<!^)(?=[A-Z])', '_', action).lower()
    if player_func in globals():
        fn = globals()[player_func]
        if callable(player_func) in fn:
            resp = fn(data)
    resp["messageId"] = message["messageId"]
    server.send_message(client, resp)


def main():
    server = websocket_server.WebsocketServer(port=8001)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()


def choose_character(data):
    index = int(data)
    if 0 > index or index > len(CHARACTERS):
        return {"success": False, "msg": "Invalid character: " + str(index), "data": {}}
    return gc.create_pc(CHARACTERS[index])


def api_attack(data):
    return gc.attack(data["character"]["name"], data["target"]["name"])


def api_cast(data):
    pass


def api_move(data):
    if "target" not in data.keys() or "pos" not in data.keys() or "real_pixels" not in data.keys():
        return {"success": "false", "msg": "Missing keys: target, pos or real_pixels", "data": {}}
    gc.move(data["target"], data["pos"], data["real_pixels"])


def api_pass_turn(data):
    pass


def api_switch_weapon(data):
    pass


### DM methods


def dm_start(data):
    return gc.start()


def dm_change_health(data):
    pass


def dm_reset(data):
    pass


def dm_continue(data):
    pass


def dm_create_npcs(data):
    if not ("allies" in data.keys() and "amount" in data.keys()):
        return {"success": False, "msg": "Missing keys: allies or amount", "data": {}}
    return gc.create_npc(data["amount"], data["allies"])


if __name__ == "__main__":
    main()
