import {useCallback, useEffect, useReducer, useRef, useState} from "react";
import Button from '@mui/material/Button';
import Token from "../elements/token";
import EventMessage from "../elements/event-message";
import "./battlemap.css";
import NpcDialog from "../elements/npc-dialog";
import ChangeCharDialog from "../elements/change-char-dialog";

const MAX_LOG_SIZE = 250;

const reducer = (gameData, action) => {
    let newGameData = {...gameData};
    switch (action.type) {
        case "setCharacter":
            newGameData.characters[action.character.id] = action.character;
            break;
        case "characterPlace":
            newGameData.characters[action.characterId].pos = action.to;
            break;
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
        case "characterSurvived":
            newGameData.characters[action.characterId].hp = action.hp
            newGameData.log.push({
                timestamp: action.timestamp,
                message: `${gameData.characters[action.characterId].name} survived due to ${action.reason}`,
                color: 'green'
            })
            break;
        default:
            break;
    }

    if (newGameData.log.length > MAX_LOG_SIZE) {
        newGameData.log = newGameData.log.slice(newGameData.log.length - MAX_LOG_SIZE);
    }

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
    const [npcDialog, setNpcDialog] = useState(false);
    const [changeChar, setChangeChar] = useState(false)
    const [round, setRound] = useState(0);
    const [gameState, setGameState] = useState("ongoing");
    const [loaded, setLoaded] = useState(false);

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
        } else {
            console.log("WARN: translatePosition called before mapRef was loaded!");
            return pos;
        }
    }

    const onCharacterUpdate = useCallback((char) => {
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
        setRound(data.round);
        setGameState(data.state);
    }, []);

    const onGameEvent = useCallback((data) => {
        if (data.type.startsWith("character")) {
            dispatch(data);
        }
    }, []);

    useEffect(() => {
        onFetchCharacters();
    }, [onFetchCharacters]);

    useEffect(() => {
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

    const tokens = Object.values(mapRef.current && loaded ? gameData.characters : {}).map(c => <Token
        character={c}
        onDrag={(e) => onTokenDrag(e, c)}
        onClick={() => setSelectedCharacter(c.id)}
        translatePosition={translatePosition}
        isSelected={c.id === selectedCharacter}
    />);

    const messages = gameData.log.map(entry => <EventMessage
        eventMessage={entry.message}
        color={entry.color}
    />);

    return <div className="battle-view">
        <div className="battlemap-container">
            <img className="battlemap" src={"/img/battlemap.png"} alt="BattleMap" ref={mapRef} onLoad={() => setLoaded(true)}/>
            {tokens}
        </div>
        <div className="event-container">
            <div className="status">
                <img className="heart" src={"/img/heart.png"} alt={"heart icon"} />
                &nbsp; {character.hp} / {character.max_hp}
                <div>Round {round}.</div>
            </div>
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
        <NpcDialog npcDialog={npcDialog} setNpcDialog={setNpcDialog} api={api}/>
        <ChangeCharDialog changeChar={changeChar} setChangeChar={setChangeChar} selectedChar={selectedCharacter} api={api}/>
    </div>

}