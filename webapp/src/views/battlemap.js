import {Box, styled} from "@mui/material";
import {useCallback, useEffect, useRef, useState} from "react";
import {target} from "../../webpack.config";

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

    const onCharacterMoved = useCallback((response) => {

        if (response.success) {
            let relWidth = Math.floor(mapRef.current.clientWidth / response.og_x);
            let relHeight = Math.floor(mapRef.current.clientHeight / response.og_y);
            let trueX = relWidth * response.x;
            let trueY = relHeight * response.y;
            setCharacters({...characters, [response.char.id]: {...characters[response.char.id], pos: [trueX, trueY]}});
        } else {
            alert("Error moving character: " + response.msg);
        }
    }, []);

    useEffect(() => {
        onFetchCharacters();
    }, [fetchCharacters, onFetchCharacters]);

    useEffect(() => {
        api.registerEvent("characterJoin", onCharacterJoin);
        api.registerEvent("move", onCharacterMoved);

        return () => {
            // dismount
            api.unregisterEvent("characterJoin");
            api.unregisterEvent("move");
        }
    }, [api, onCharacterJoin]);

    const onTokenDrag = useCallback((event, char) => {
        let pos = event.target.getBoundingClientRect();
        if (character.id === char.id) {
            let params = {
                "target": char.id,
                "real_pixels": [mapRef.current.clientHeight, mapRef.current.clientWidth]
            }
            api.sendRequest("move", params)
        } else if (role === "dm") {
            let params = {
                "target": char.id,
                "pos": [pos.x, pos.y],
                "real_pixels": [mapRef.current.clientHeight, mapRef.current.clientWidth]
            }
            api.sendRequest("dm_move", params)
        }
    }, [api]);

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