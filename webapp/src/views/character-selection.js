import {useCallback, useEffect, useState} from "react";
import CharacterToken from "../elements/character-token";
import DMToken from "../elements/dm-token";
import {Alert, Box, Button, CircularProgress, styled, TextField} from "@mui/material";

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
    display: "block",
    marginTop: theme.spacing(2),
    marginLeft: "auto",
    marginRight: "auto",
}));

const StartButton = styled(Button)(({theme}) => ({
    display: "block",
    marginTop: theme.spacing(2),
    marginLeft: "auto",
    marginRight: "auto",
}));

export default function CharacterSelection(props) {

    const onSelectCharacter = props.onSelectCharacter;
    const api = props.api;
    const onSelectRole = props.onSelectRole;

    const [characters, setCharacters] = useState(null);
    const [fetchCharacters, setFetchCharacters] = useState(true);
    const [selectedCharacter, setSelectedCharacter] = useState(null);
    const [error, setError] = useState(null);
    const [showPasswordPrompt, setShowPasswordPrompt] = useState(false);
    const [password, setPassword] = useState("");

    const onFetchCharacters = useCallback((force = false) => {
        setFetchCharacters(false);
        setError(null);
        api.getSelectableCharacters((response) => {
            if (response.success) {
                setCharacters(response.data);
            } else {
                setError(response.msg);
            }
        });
    }, [api]);

    const onChooseCharacter = useCallback(() => {
        setError(null);
        api.onChooseCharacter(selectedCharacter, (response) => {
            if (response.success) {
                onSelectCharacter(response.data.character);
                onSelectRole(response.data.role);
            } else {
                setError(response.msg);
            }
        }, password)
    }, [api, onSelectCharacter, selectedCharacter, password, onSelectRole]);

    useEffect(() => {
        if (characters === null || fetchCharacters) {
            onFetchCharacters();
        }
        setShowPasswordPrompt(selectedCharacter === "Crab");
    }, [fetchCharacters, characters, onFetchCharacters, setShowPasswordPrompt, selectedCharacter]);

    const renderCharacter = (name, character) => {
        if (character.name.toLowerCase() !== "crab") {
            let style = selectedCharacter === name ? {borderColor: "red"} : {};
            return <CharacterToken key={`character-${character.name}`}
                                   onClick={() => setSelectedCharacter(selectedCharacter === name ? null : name)}
                                   style={style}>
                <img src={character.token} alt={`[token of ${character.name}]`} title={`Choose ${character.name}`}/>
            </CharacterToken>
        }
    };

    if (!characters) {
        return <CircularProgress />
    }

    return <>
        <CharacterContainer>
            <div><h2>Choose your character</h2></div>
            <div>
                {characters
                    ? <>
                        <div>
                            {Object.keys(characters).map((name) => renderCharacter(name, characters[name]))}
                        </div>
                        <CharacterName size={"small"} variant={"outlined"}
                                       sx={{input: {color: 'white', borderColor: 'white', backgroundColor: '#3c3e42ff'}}}
                                       placeholder={"Charactername"}
                                       slotProps={{htmlInput: {min: 0, style: {textAlign: 'center'}}}}
                                       readOnly={true} value={characters[selectedCharacter]?.name || ""}/>
                        <StartButton variant={"outlined"} onClick={() => onChooseCharacter()}
                                     disabled={selectedCharacter === null}>
                            Start
                        </StartButton>
                    </>
                    : <CircularProgress/>
                }
                <Box marginTop={2}>
                    <DMToken 
                        character={characters["crab"]}
                        onClick={() => setSelectedCharacter(selectedCharacter === "Crab" ? null : "Crab")}
                        isSelected={selectedCharacter === "Crab"} />
                    {showPasswordPrompt ? <Box marginTop={2}>
                            <TextField type={"password"} placeholder="DM Password" value={password} 
                                slotProps={{htmlInput: {min: 0, style: {textAlign: 'center'}}}}
                                sx={{input: {color: 'white', borderColor: 'white', backgroundColor: '#3c3e42ff'}}}
                                onChange={e => setPassword(e.target.value)}/>
                        </Box>
                        : null}
                </Box>
            </div>
            {error ?
                <Alert severity={"error"} title={"An error occured"}>{error}</Alert> : <></>
            }
        </CharacterContainer>
    </>

}