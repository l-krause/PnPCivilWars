import {useCallback, useEffect, useState} from "react";
import {Box, CircularProgress, styled, TextField} from "@mui/material";

const CharacterToken = styled(Box)(({theme}) => ({
    "& img": {
      width: 128,
      height: 128,
      padding: theme.spacing(2),
    },
    cursor: "pointer",
    display: "inline-block",
    borderColor: "transparent",
    borderWidth: 1,
    borderRadius: 5,
    borderStyle: "solid",
    "&:hover": {
        borderColor: "#ccc",
        backgroundColor: "#f0f0f0"
    }
}));

const CharacterContainer = styled(Box)(({theme}) => ({
    marginLeft: "auto",
    marginRight: "auto",
    maxWidth: "80%",
    "& > div": {
        textAlign: "center",
    }
}));

const CharacterName = styled(TextField)(({theme}) => ({
    width: 300,
    marginTop: theme.spacing(2)
}));

export default function CharacterSelection(props) {

    const onSelectCharacter = props.onSelectCharacter;
    const api = props.api;

    const [characters, setCharacters] = useState(null);
    const [fetchCharacters, setFetchCharacters] = useState(true);
    const [selectedCharacter, setSelectedCharacter] = useState(null);
    const [error, setError] = useState(null);

    const onFetchCharacters = useCallback((force = false) => {
        setFetchCharacters(false);
        api.getPlayableCharacters((data) => {
            if (data.success) {
                setCharacters(data.data);
            } else {
                setError(data.msg);
            }
        });
    }, [api]);

    const onRequestCharacter = useCallback((c) => {

    }, []);

    useEffect(() => {
        if (characters === null || fetchCharacters) {
            onFetchCharacters();
        }
    }, [fetchCharacters, characters, onFetchCharacters]);

    const renderCharacter = (name, character) => {
        let style = selectedCharacter === name ? { borderColor: "red" } : {};
        return <CharacterToken onClick={() => setSelectedCharacter(selectedCharacter === name ? null : name)} style={style}>
                <img src={character.token} alt={`[token of ${character.name}]`} title={`Choose ${character.name}`} />
            </CharacterToken>
    };

    return <>
        <CharacterContainer>
            <div><h2>Choose your character first!</h2></div>
            <div>
                { characters
                    ? <>
                        <div>
                            {Object.keys(characters).map((name) => renderCharacter(name, characters[name]))}
                        </div>
                        <CharacterName size={"small"} variant={"outlined"}
                                       sx={{ input: { color: 'white', borderColor: 'white' } }}
                                       placeholder={"Charactername"}
                                       inputProps={{min: 0, style: { textAlign: 'center' }}}
                                       readOnly={true} value={characters[selectedCharacter]?.name || ""} />
                    </>
                    : <CircularProgress />
                }
            </div>
        </CharacterContainer>
    </>

}