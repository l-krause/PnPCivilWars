import {Box, styled} from "@mui/material";
import {useCallback, useEffect, useState} from "react";

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

    const [fetchCharacters, setFetchCharacters] = useState(true);
    const [characters, setCharacters] = useState({});

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

    useEffect(() => {
        onFetchCharacters();
    }, [fetchCharacters, onFetchCharacters]);

    useEffect(() => {
        api.registerEvent("characterJoin", onCharacterJoin);
        return () => {
            // dismount
            api.unregisterEvent("characterJoin");
        }
    }, [api, onCharacterJoin]);

    const renderCharacter = (character) => {
        return <Token key={"character-" + character.id} style={{ left: character.pos[0], top: character.pos[1] }}>
                <img alt={"token of " + character.id} src={character.token} />
            </Token>
    };

    console.log(characters);

    const tokens = Object.values(characters).map(c => renderCharacter(c));
    /*tokens.push(renderCharacter(character));*/

    return <MapContainer>
        <div>
            <img src={"/img/battlemap.png"} alt="BattleMap"/>
            { tokens }
        </div>
    </MapContainer>

}