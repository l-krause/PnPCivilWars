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
    const [buttonDisabled, setButtonDisabled] = useState(true);
    const [activeChar, setActiveChar] = useState(null);
    const mapRef = useRef(null);

    const onFetchCharacters = useCallback(() => {
        if (fetchCharacters) {
            setFetchCharacters(false);
            api.fetchAllCharacters((response) => {
                if (response.success) {
                    setCharacters(response.data);
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
        newState[char.id] = char;
        setCharacters(newState);
    }, [setCharacters, characters]);

    const onStartGame = useCallback((response) => {
        setActiveChar(response.data["first"])
    }, [setActiveChar])

    const onReset = useCallback((response) => {
        setCharacter(null);
    }, [setCharacter])

    useEffect(() => {
        onFetchCharacters();
    }, [fetchCharacters, onFetchCharacters]);

    useEffect(() => {
        api.registerEvent("characterJoin", onCharacterJoin);
        api.registerEvent("characterUpdate", onCharacterUpdate);
        api.registerEvent("start", onStartGame);
        api.registerEvent("reset", onReset);

        return () => {
            // dismount
            api.unregisterEvent("characterJoin");
            api.unregisterEvent("characterUpdate");
            api.unregisterEvent("start");
            api.unregisterEvent("reset");
        }
    }, [api, onCharacterJoin, onCharacterUpdate, onStartGame, onReset]);

    const onTokenDrag = useCallback((e, char) => {
        let img = mapRef.current;
        if (img) {
            console.log(e);
            let rect = e.target.getBoundingClientRect();
            let pos = {x: e.clientX - rect.left, y: e.clientY - rect.top};
            let relWidth = Math.floor(img.clientWidth / img.naturalWidth);
            let relHeight = Math.floor(img.clientHeight / img.naturalHeight);
            let trueX = relWidth * pos.x;
            let trueY = relHeight * pos.y;

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
            <img alt={"token of " + character.id} src={character.token} onDragEnd={(e) => onTokenDrag(e, character)}/>
        </Token>
    };

    console.log(characters);

    const tokens = Object.values(characters).map(c => renderCharacter(c));
    /*tokens.push(renderCharacter(character));*/

    const onAction = (action) => {
        api.sendRequest(action, {"target": selectedCharacter})
    }

    const onPassTurn = () => {
    }

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
                <Button variant="contained" onClick={() => onPassTurn()} disabled={activeChar !== character}>Pass
                    Turn</Button>
            </div> :
            <div>
                <Button variant="contained" onClick={() => onAction("start")}>Start</Button>
                <Button variant="contained" onClick={() => onAction("continue")}>Continue</Button>
                <Button variant="contained" onClick={() => onAction("reset")}>Reset</Button>
            </div>}
    </div>

}