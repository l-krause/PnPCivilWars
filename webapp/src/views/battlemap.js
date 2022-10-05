import {
    Box,
    Checkbox,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    styled,
    TextField
} from "@mui/material";
import {useCallback, useEffect, useReducer, useRef, useState} from "react";
import Button from '@mui/material/Button';
import Token from "../elements/token";
import EventMessage from "../elements/event-message";
import "./battlemap.css";

const MAX_LOG_SIZE = 250;

const MapContainer = styled(Box)(({theme}) => ({
    "& > div": {
        position: "relative",
        width: "min-content",
        marginLeft: "auto",
        marginRight: "auto",
        marginTop: theme.spacing(2),
        border: "1px solid white"
    }
}));

const reducer = (gameData, action) => {
    console.log("BEFORE", gameData);
    let newGameData = {...gameData};
    switch (action.type) {
        case "setCharacter":
            newGameData.characters[action.character.id] = action.character;
            break;
        case "characterPlace":
        case "characterMove":
            newGameData.characters[action.characterId].pos = action.to;
            // newGameData.log.push({
            //     timestamp: action.timestamp,
            //     message: `Character id=${action.characterId} moved to pos=(${action.to.x}, ${action.to.y})`
            // });
            break;
        case "setAllCharacters":
            newGameData.characters = action.characters;
            break;
        case "addCharacters":
            for (const char of action.characters) {
                newGameData.characters[char.id] = char;
            }
            break;
        case "characterDied":
            newGameData.characters[action.characterId].status = "dead";
            newGameData.log.push({
                timestamp: action.timestamp,
                message: `${gameData.characters[action.characterId].name} died, reason=${action.reason}`,
                color: "red"
            });
            break;
        case "characterAttack":
            newGameData.characters[action.victim].hp = newGameData.characters[action.victim].hp - action.damage;
            newGameData.log.push({
                    timestamp: action.timestamp,
                    message: `${gameData.characters[action.attacker].name} hit ${gameData.characters[action.victim].name} with a ${action.hit} for ${action.damage} damage!`,
                    color: "white"
                }
            )
            break;
        default:
            break;
    }

    if (newGameData.log.length > MAX_LOG_SIZE) {
        newGameData.log = newGameData.log.slice(newGameData.log.length - MAX_LOG_SIZE);
    }

    console.log("AFTER", newGameData);
    return newGameData;
}

export default function BattleMap(props) {

    const api = props.api;
    const character = props.character;
    const role = props.role;
    const setCharacter = props.setCharacter;

    const [fetchCharacters, setFetchCharacters] = useState(true);
    const [gameData, dispatch] = useReducer(reducer, null, () => ({characters: {}, log: []}));
    const [selectedCharacter, setSelectedCharacter] = useState(null);
    const [activeChar, setActiveChar] = useState(null);
    const [npcAmount, setNPCAmount] = useState(20);
    const [npcAlly, setNPCAlly] = useState(true);
    const [npcDialog, setNpcDialog] = useState(false);
    const [changeChar, setChangeChar] = useState(false)
    const [changeHp, setChangeHp] = useState(0);
    const [changeMaxHp, setChangeMaxHp] = useState(0);
    const [changeDamage, setChangeDamage] = useState(0);
    const [changeAdd, setChangeAdd] = useState(0);
    const [changeArmor, setChangeArmor] = useState(0);
    const [changeDice, setChangeDice] = useState(0);
    const mapRef = useRef(null);

    const onFetchCharacters = useCallback(() => {
        if (fetchCharacters) {
            setFetchCharacters(false);
            api.fetchAllCharacters((response) => {
                if (response.success) {
                    dispatch({type: "setAllCharacters", characters: response.data});
                } else {
                    alert("Error fetching characters: " + response.msg);
                }
            });
        }
    }, [api, fetchCharacters]);

    const onCharacterJoin = useCallback((character) => {
        if (!gameData.characters.hasOwnProperty(character.id)) {
            dispatch({type: "setCharacter", character: character});
        }
    }, [gameData]);

    const translatePosition = (pos) => {
        let img = mapRef.current;
        if (img) {
            let relY = img.clientHeight / img.naturalHeight;
            let relX = img.clientWidth / img.naturalWidth;
            let x = Math.floor(relX * pos.x);
            let y = Math.floor(relY * pos.y);
            return {x: x, y: y};
        }

        return null;
    }

    const onCharacterUpdate = useCallback((char) => {
        char.pos = translatePosition(char.pos);
        dispatch({type: "setCharacter", character: char});
    }, []);

    const onReset = useCallback((response) => {
        setCharacter(null);
    }, [setCharacter]);

    const onAction = useCallback((action) => {
        api.sendRequest(action, {"target": selectedCharacter})
    }, [api, selectedCharacter]);

    const onCreatedNpcs = useCallback((data) => {
        if (data.success) {
            let newChars = [];
            // villagers/veterans/... => list of chars
            for (const chars of Object.values(data.data)) {
                newChars = newChars.concat(newChars, chars);
            }
            dispatch({type: "addCharacters", characters: newChars});
        } else {
            alert(data.msg);
        }
    }, []);

    const onGameStatus = useCallback((data) => {
        setActiveChar(data.active_char);
        // setRound(data.round);
        // setGameState(data.state);
    }, []);

    const onGameEvent = useCallback((data) => {
        if (data.type.startsWith("character")) {
            if (data.type === "characterMove" || data.type === "characterPlace") {
                data.to = translatePosition(data.to);
            }
            dispatch(data);
        }
    }, []);

    useEffect(() => {
        onFetchCharacters();
    }, [onFetchCharacters]);

    useEffect(() => {
        console.log("useEffect called");
        api.registerEvent("characterJoin", onCharacterJoin);
        api.registerEvent("characterUpdate", onCharacterUpdate);
        api.registerEvent("start", (res) => !res.success && alert("Error starting game: " + res.msg));
        api.registerEvent("reset", onReset);
        api.registerEvent("pass", (res) => !res.success && alert("Error passing turn: " + res.msg));
        api.registerEvent("createNPCs", onCreatedNpcs);
        api.registerEvent("gameStatus", onGameStatus);
        api.registerEvent("gameEvent", onGameEvent);

        return () => {
            // dismount
            api.unregisterEvent("characterJoin");
            api.unregisterEvent("characterUpdate");
            api.unregisterEvent("start");
            api.unregisterEvent("reset");
            api.unregisterEvent("pass");
            api.unregisterEvent("createNPCs");
            api.unregisterEvent("gameStatus");
            api.unregisterEvent("gameEvent");
        }
    }, [api, onCharacterJoin, onCharacterUpdate, onReset, onCreatedNpcs, onGameStatus, onGameEvent]);

    const onTokenDrag = useCallback((e, char) => {
        let img = mapRef.current;
        if (img) {
            console.log(e);
            e.preventDefault();
            let rect = img.getBoundingClientRect();
            let pos = {x: e.clientX - rect.x, y: e.clientY - rect.y};
            let relWidth = img.naturalWidth / img.clientWidth;
            let relHeight = img.naturalHeight / img.clientHeight;
            let trueX = Math.floor(relWidth * pos.x);
            let trueY = Math.floor(relHeight * pos.y);

            let params = {
                "pos": [trueX, trueY],
            }

            if (character.id === activeChar) {
                api.sendRequest("move", params, (response) => {
                    if (!response.success) {
                        alert("Error moving character: " + response.msg);
                    }
                });
            } else {
                if (role === "dm") {
                    params["target"] = char.id;
                    api.sendRequest("place", params, (response) => {
                        if (!response.success) {
                            alert("Error placing: " + response.msg);
                        }
                    })
                }
            }
        }


    }, [api, character, role, activeChar]);

    const addNpcs = () => {
        let data = {"allies": npcAlly, "amount": parseInt(npcAmount + "")}
        api.sendRequest("createNPCs", data)
    };

    const changeSelCharacter = () => {
        let data = {
            "character": selectedCharacter,
            "curr_hp": changeHp,
            "max_hp": changeMaxHp,
            "dice": changeDice,
            "damage": changeDamage,
            "modifier": changeAdd,
            "armor": changeArmor
        }
        api.sendRequest("changeSelChar", data)
    }


    const tokens = Object.values(gameData.characters).map(c => <Token
        character={c}
        onDrag={(e) => onTokenDrag(e, c)}
        onClick={() => setSelectedCharacter(c.id)}
        isSelected={c.id === selectedCharacter}
    />);
    const messages = gameData.log.map(entry => <EventMessage
        eventMessage={entry.message}
        color={entry.color}
    />);


    return <div className="battle-view">
        <div className="battlemap-container">
            <img className="battlemap" src={"/img/battlemap.png"} alt="BattleMap" ref={mapRef}/>
            {tokens}
        </div>
        <div className="event-container">
            <div className="event-log">
                {messages}
            </div>
            <div className="question"><h4>How do you want to spend your action point?</h4></div>
            {role !== "dm" || (activeChar === character.id) ? <div className="player-interface">
                    <Button variant="contained" onClick={() => onAction("attack")}
                            disabled={activeChar !== character.id}>Attack</Button>
                    <Button variant="contained" onClick={() => onAction("spell")}
                            disabled={activeChar !== character.id}>Spell</Button>
                    <Button variant="contained" onClick={() => api.sendRequest("dash")}
                            disabled={activeChar !== character.id}>Dash</Button>
                    <Button variant="contained" disabled={activeChar !== character.id}>Change Weapon</Button>
                    <Button className="pass-turn" variant="contained" onClick={() => onAction("pass")}
                            disabled={activeChar !== character.id}>Pass
                        Turn</Button>
                </div> :
                <div className="dm-interface">
                    <Button variant="contained" onClick={() => onAction("start")}>Start</Button>
                    <Button variant="contained" onClick={() => onAction("continue")}>Continue</Button>
                    <Button variant="contained" onClick={() => onAction("reset")}>Reset</Button>
                    <Button variant="contained" onClick={() => onAction("changeHealth")}>Change HP</Button>
                    <Button variant="contained" onClick={() => onAction("kill")}>Kill</Button>
                    <Button variant="contained" onClick={() => onAction("stun")}>Stun</Button>
                    <Button variant="contained" onClick={() => setNpcDialog(true)}>Create NPCs</Button>
                    <Button variant="contained" onClick={() => setChangeChar(true)}>Change Character</Button>
                </div>}
        </div>
        <Dialog open={npcDialog} onClose={() => setNpcDialog(false)}>
            <DialogTitle>Create NPCs</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    Choose how many NPCs to create and if they should be created as allies.
                </DialogContentText>
                <TextField label="Amount" value={npcAmount} onChange={e => setNPCAmount(e.target.value)}/>
                <Checkbox label={"Ally?"} checked={npcAlly} onChange={() => setNPCAlly(!npcAlly)}/>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => {
                    addNpcs();
                    setNpcDialog(false);
                }}>Create</Button>
                <Button onClick={() => setNpcDialog(false)}>Cancel</Button>
            </DialogActions>
        </Dialog>
        <Dialog open={changeChar} onClose={() => setChangeChar(false)}>
            <DialogTitle>Create NPCs</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    Choose how you want to modify the character
                </DialogContentText>
                <TextField label="Max HP" value={changeMaxHp} onChange={e => setChangeMaxHp(e.target.value)}/>
                <TextField label="Curr_HP" value={changeHp} onChange={e => setChangeHp(e.target.value)}/>
                <TextField label="Damage Dice" value={changeDice} onChange={e => setChangeDice(e.target.value)}/>
                <TextField label="Dice Type" value={changeDamage} onChange={e => setChangeDamage(e.target.value)}/>
                <TextField label="Damage Additional" value={changeAdd} onChange={e => setChangeAdd(e.target.value)}/>
                <TextField label="Armor" value={changeArmor} onChange={e => setChangeArmor(e.target.value)}/>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => {
                    changeSelCharacter();
                    setChangeChar(false);
                }}>Change</Button>
                <Button onClick={() => setChangeChar(false)}>Cancel</Button>
            </DialogActions>
        </Dialog>
    </div>

}