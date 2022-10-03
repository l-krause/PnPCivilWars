import {Box, Checkbox, styled, TextField} from "@mui/material";
import {useCallback, useEffect, useRef, useState} from "react";
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

export default function BattleMap(props) {

    const api = props.api;
    const character = props.character;
    const role = props.role;
    const setCharacter = props.setCharacter;

    const [fetchCharacters, setFetchCharacters] = useState(true);
    const [characters, setCharacters] = useState({});
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
                    setCharacters(response.data);
                } else {
                    alert("Error fetching characters: " + response.msg);
                }
            });
        }
    }, [api, fetchCharacters]);

    const onCharacterJoin = useCallback((character) => {
        if (!characters.hasOwnProperty(character.id)) {
            setCharacters({...characters, [character.id]: character})
        }
    }, [characters]);

    const onCharacterUpdate = useCallback((char) => {
        let newState = {...characters};
        if (JSON.stringify(char.pos) !== JSON.stringify(characters[char.id].pos)) {
            let img = mapRef.current;
            if (img) {
                let rect = img.getBoundingClientRect();
                let relY = img.clientHeight / img.naturalHeight;
                let relX = img.clientWidth / img.naturalWidth;
                char.pos.x = Math.floor(relY * char.pos.y) - rect.x;
                char.pos.y = Math.floor(relX * char.pos.x) - rect.y;
            }
        }
        newState[char.id] = char;
        setCharacters(newState);
    }, [characters]);

    const onStartGame = useCallback((response) => {
        setActiveChar(response.data["first"]);
    }, [setActiveChar]);

    const onReset = useCallback((response) => {
        setCharacter(null);
    }, [setCharacter]);

    const onAction = useCallback((action) => {
        api.sendRequest(action, {"target": selectedCharacter})
    }, [api, selectedCharacter]);

    const onPassTurn = useCallback((data) => {
        setActiveChar(data.active_char.id)
    }, [setActiveChar]);

    const onCreatedNpcs = useCallback((data) => {
        if (data.success) {
            let newChars = {...characters};
            // villagers/veterans/... => list of chars
            for (const chars of Object.values(data.data)) {
                newChars = {...newChars, ...chars};
            }
            setCharacters(newChars);
        } else {
            alert(data.msg);
        }
    }, [characters, setCharacters]);


    useEffect(() => {
        onFetchCharacters();
    }, [onFetchCharacters]);

    useEffect(() => {
        console.log("useEffect called");
        api.registerEvent("characterJoin", onCharacterJoin);
        api.registerEvent("characterUpdate", onCharacterUpdate);
        api.registerEvent("start", onStartGame);
        api.registerEvent("reset", onReset);
        api.registerEvent("pass", onPassTurn);
        api.registerEvent("createNPCs", onCreatedNpcs);

        return () => {
            // dismount
            api.unregisterEvent("characterJoin");
            api.unregisterEvent("characterUpdate");
            api.unregisterEvent("start");
            api.unregisterEvent("reset");
            api.unregisterEvent("pass");
            api.unregisterEvent("createNPCs");
        }
    }, [api, onCharacterJoin, onCharacterUpdate, onStartGame, onReset, onPassTurn, onCreatedNpcs]);

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

            if (role === "dm") {
                params["target"] = char.id;
                api.sendRequest("place", params, (response) => {
                    if (!response.success) {
                        alert("Error placing: " + response.msg);
                    }
                })
            } else {
                api.sendRequest("move", params, (response) => {
                    if (!response.success) {
                        alert("Error moving character: " + response.msg);
                    }
                });
            }
        }


    }, [api, character, role]);

    const renderCharacter = (character) => {
        let style = {};
        if (character.id === selectedCharacter) {
            style.border = "1px solid red";
        }
        if (character.type === "npc") {
            if (character.is_ally) {
                style.background = "linear-gradient(blue)";
            } else {
                style.background = "linear-gradient(red)";
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
        let data = {"allies": npcAlly, "amount": npcAmount}
        api.sendRequest("createNPCs", data)
    };

    const tokens = Object.values(characters).map(c => renderCharacter(c));

    console.log(activeChar, character);

    return <div>
        <MapContainer>
            <div>
                <img src={"/img/battlemap.png"} alt="BattleMap" ref={mapRef}/>
                {tokens}
            </div>
        </MapContainer>
        <div><h2>How do you want to spend your action point?</h2></div>
        {role !== "dm" ? <div>
                <Button variant="contained" onClick={() => onAction("attack")}
                        disabled={activeChar !== character}>Attack</Button>
                <Button variant="contained" onClick={() => onAction("spell")}
                        disabled={activeChar !== character}>Spell</Button>
                <Button variant="contained" onClick={() => api.sendRequest("dash")}
                        disabled={activeChar !== character}>Dash</Button>
                <Button variant="contained" disabled={activeChar !== character}>Change Weapon</Button>
                <Button variant="contained" onClick={() => onAction("pass")} disabled={activeChar !== character}>Pass
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