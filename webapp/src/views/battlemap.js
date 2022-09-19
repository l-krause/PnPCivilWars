import {Box, styled} from "@mui/material";
import {useCallback, useEffect, useRef, useState} from "react";

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

    const [fetchCharacters, setFetchCharacters] = useState(true);
    const [characters, setCharacters] = useState({});
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
        let newState = { ...characters };
        newState[char.id] = char;
        setCharacters(newState);
    }, [characters]);

    useEffect(() => {
        onFetchCharacters();
    }, [fetchCharacters, onFetchCharacters]);

    useEffect(() => {
        api.registerEvent("characterJoin", onCharacterJoin);
        api.registerEvent("characterUpdate", onCharacterUpdate);

        return () => {
            // dismount
            api.unregisterEvent("characterJoin");
            api.unregisterEvent("characterUpdate");
        }
    }, [api, onCharacterJoin, onCharacterUpdate]);

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

            if (character.id !== char.id) {
                if (role === "dm") {
                    params["target"] = char.id;
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


    }, [api, character.id, role]);

    const renderCharacter = (character) => {
        return <Token key={"character-" + character.id} style={{left: character.pos[0], top: character.pos[1]}}>
            <img alt={"token of " + character.id} src={character.token} onDragEnd={(e) => onTokenDrag(e, character)}/>
        </Token>
    };

    console.log(characters);

    const tokens = Object.values(characters).map(c => renderCharacter(c));
    /*tokens.push(renderCharacter(character));*/

    return <MapContainer>
        <div>
            <img src={"/img/battlemap.png"} alt="BattleMap" ref={mapRef}/>
            {tokens}
        </div>
    </MapContainer>

}