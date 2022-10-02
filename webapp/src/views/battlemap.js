import {Box, styled} from "@mui/material";
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
                let relY = img.clientHeight / img.naturalHeight;
                let relX = img.clientWidth / img.naturalWidth;
                let trueY = Math.floor(relY * char.pos[1]);
                let trueX = Math.floor(relX * char.pos[0]);
                char.pos = [trueX, trueY];
            }
        }
        newState[char.id] = char;
        setCharacters(newState);
    }, [characters]);

    const onStartGame = useCallback((response) => {
        setActiveChar(response.data["first"]);
        console.log(activeChar, character);
    }, [activeChar, setActiveChar]);

    const onReset = useCallback((response) => {
        setCharacter(null);
    }, [setCharacter]);

    const onAction = useCallback((action) => {
        api.sendRequest(action, {"target": selectedCharacter})
    }, [api, selectedCharacter]);

    const onPassTurn = useCallback((data) => {
        setActiveChar(data.active_char.id)
    }, [setActiveChar]);


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

        return () => {
            // dismount
            api.unregisterEvent("characterJoin");
            api.unregisterEvent("characterUpdate");
            api.unregisterEvent("start");
            api.unregisterEvent("reset");
            api.unregisterEvent("pass");
        }
    }, [api, onCharacterJoin, onCharacterUpdate, onStartGame, onReset]);

    const onTokenDrag = useCallback((e, char) => {
        let img = mapRef.current;
        if (img) {
            console.log(e);
            let pos = {x: e.clientX, y: e.clientY};
            let relWidth = img.naturalWidth / img.clientWidth;
            let relHeight =img.naturalHeight / img.clientHeight;
            let trueX = Math.floor(relWidth * pos.x);
            let trueY = Math.floor(relHeight * pos.y);

            let params = {
                "pos": [trueX, trueY],
                "real_pixels": [img.clientHeight, img.clientWidth]
            }

            if (!character || character.id !== char.id) {
                if (role === "dm") {
                    params["target"] = char.id;
                    api.sendRequest("place", params, (response) => {
                        if (!response.success) {
                            alert("Error placing: " + response.msg);
                        }
                    })
                    return;
                } else {
                    e.preventDefault();
                    return;
                }
            }


            api.sendRequest("move", params, (response) => {
                if (!response.success) {
                    alert("Error moving character: " + response.msg);
                }
            });
        }


    }, [api, character, role]);

    const renderCharacter = (character) => {
        return <Token key={"character-" + character.id} style={{left: character.pos[0], top: character.pos[1]}}>
            <img alt={"token of " + character.id} src={character.token}
                 onDragEnd={(e) => onTokenDrag(e, character)}
                 onClick={() => setSelectedCharacter(character.id)}
                 style={character.id === selectedCharacter ? { border: "1px solid red"} : {}}/>
        </Token>
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
                <Button variant="contained" onClick={() => onAction("createNPCs")}>Create NPCs</Button>
            </div>}
    </div>

}