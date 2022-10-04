import {Box, Checkbox, styled, TextField} from "@mui/material";
import {useCallback, useEffect, useReducer, useRef, useState} from "react";
import Button from '@mui/material/Button';

const TOKEN_SIZE = 48;

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

const Token = styled(Box)(({theme}) => ({
    position: "absolute",
    "& img": {
        width: TOKEN_SIZE,
        height: TOKEN_SIZE
    }
}));

const reducer = (characters, action) => {
    console.log("BEFORE", characters);
    let newCharacters = {...characters};
    switch (action.type) {
        case "setCharacter":
            newCharacters[action.character.id] = action.character;
            break;
        case "characterPlace":
        case "characterMove":
            newCharacters[action.characterId] = { ...newCharacters[action.characterId], pos: action.to };
            break;
        case "setAllCharacters":
            newCharacters = action.characters;
            break;
        case "addCharacters":
            for(const char of action.characters) {
                newCharacters[char.id] = char;
            }
            break;
        default:
            break;
    }

    console.log("AFTER", newCharacters);
    return newCharacters;
}

export default function BattleMap(props) {

    const api = props.api;
    const character = props.character;
    const role = props.role;
    const setCharacter = props.setCharacter;

    const [fetchCharacters, setFetchCharacters] = useState(true);
    const [characters, dispatch] = useReducer(reducer, null, () => ({}));
    const [selectedCharacter, setSelectedCharacter] = useState(null);
    const [activeChar, setActiveChar] = useState(null);
    const [npcAmount, setNPCAmount] = useState(20);
    const [npcAlly, setNPCAlly] = useState(true);
    const mapRef = useRef(null);

    const onFetchCharacters = useCallback(() => {
        if (fetchCharacters) {
            setFetchCharacters(false);
            api.fetchAllCharacters((response) => {
                if (response.success) {
                    dispatch({ type: "setAllCharacters", characters: response.data });
                } else {
                    alert("Error fetching characters: " + response.msg);
                }
            });
        }
    }, [api, fetchCharacters]);

    const onCharacterJoin = useCallback((character) => {
        if (!characters.hasOwnProperty(character.id)) {
            dispatch({ type: "setCharacter", character: character });
        }
    }, [characters]);

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
            dispatch({ type: "addCharacters", characters: newChars });
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
        if (data.type === "characterMove") {
            data.to = translatePosition(data.to);
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

            if (character.id === activeChar){
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

    const renderCharacter = (character) => {
        let style = {};
        if (character.id === selectedCharacter) {
            style.border = "1px solid red";
        }
        if (character.type === "npc") {
            if (character.is_ally) {
                style.filter = " hue-rotate(180deg)";
            }
        }
        return <Token key={"character-" + character.id} style={{left: character.pos.x, top: character.pos.y}}>
            <img alt={"token of " + character.id} src={character.token}
                 onDragEnd={(e) => onTokenDrag(e, character)}
                 onClick={() => setSelectedCharacter(character.id)}
                 style={style}/>
        </Token>
    };

    const addNpcs = () => {
        let data = {"allies": npcAlly, "amount": parseInt(npcAmount + "")}
        api.sendRequest("createNPCs", data)
    };

    const tokens = Object.values(characters).map(c => renderCharacter(c));

    return <div>
        <MapContainer>
            <div>
                <img src={"/img/battlemap.png"} alt="BattleMap" ref={mapRef}/>
                {tokens}
            </div>
        </MapContainer>
        <div><h2>How do you want to spend your action point?</h2></div>
        {role !== "dm" || (activeChar === character.id) ? <div>
                <Button variant="contained" onClick={() => onAction("attack")}
                        disabled={activeChar !== character.id}>Attack</Button>
                <Button variant="contained" onClick={() => onAction("spell")}
                        disabled={activeChar !== character.id}>Spell</Button>
                <Button variant="contained" onClick={() => api.sendRequest("dash")}
                        disabled={activeChar !== character.id}>Dash</Button>
                <Button variant="contained" disabled={activeChar !== character.id}>Change Weapon</Button>
                <Button variant="contained" onClick={() => onAction("pass")} disabled={activeChar !== character.id}>Pass
                    Turn</Button>
            </div> :
            <div>
                <Button variant="contained" onClick={() => onAction("start")}>Start</Button>
                <Button variant="contained" onClick={() => onAction("continue")}>Continue</Button>
                <Button variant="contained" onClick={() => onAction("reset")}>Reset</Button>
                <Button variant="contained" onClick={() => onAction("changeHealth")}>Change HP</Button>
                <Button variant="contained" onClick={() => onAction("kill")}>Kill</Button>
                <Button variant="contained" onClick={() => onAction("stun")}>Stun</Button>
                <Button variant="contained" onClick={() => addNpcs()}>Create NPCs</Button>
                <TextField label="Amount" value={npcAmount} onChange={e => setNPCAmount(e.target.value)}/>
                <Checkbox label={"Ally?"} checked={npcAlly} onChange={() => setNPCAlly(!npcAlly)}/>
            </div>}
    </div>

}