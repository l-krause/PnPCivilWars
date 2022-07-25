import websocket_server
import json

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
    if action == "chooseCharacter":
        resp = choose_character(int(data))
    if action == "attack":
        pass
    if action == "cast":
        pass
    if action == "move":
        pass
    if action == "pass":
        pass
    if action == "switch_weapon":
        pass
    # dm
    if action == "start":
        pass
    if action == "changeHealth":
        pass
    if action == "setPosition":
        pass
    if action == "reset":
        pass
    if action == "createNpcs":
        resp = create_npcs(data)
    if action == "continue":
        pass
    resp["messageId"] = message["messageId"]
    server.send_message(client, resp)


def main():
    server = websocket_server.WebsocketServer(port=8001)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()


def choose_character(index: int):
    if 0 > index or index > len(CHARACTERS):
        return {"success": False, "msg": "Invalid character: " + str(index), "data": {}}
    return gc.create_pc(CHARACTERS[index])


def create_npcs(data):
    if not ("allies" in data.keys() and "amount" in data.keys()):
        return {"success": False, "msg": "Missing keys: allies or amount", "data": {}}
    return gc.create_npc(data["amount"], data["allies"])


if __name__ == "__main__":
    main()
