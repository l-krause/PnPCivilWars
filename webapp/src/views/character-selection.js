import {useCallback, useEffect, useState} from "react";
import {Alert, Box, Button, CircularProgress, styled, TextField} from "@mui/material";
import CloseIcon from '@mui/icons-material/Close';

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
    }, [api, onSelectCharacter, selectedCharacter, setShowPasswordPrompt]);

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
                                       sx={{input: {color: 'white', borderColor: 'white'}}}
                                       placeholder={"Charactername"}
                                       inputProps={{min: 0, style: {textAlign: 'center'}}}
                                       readOnly={true} value={characters[selectedCharacter]?.name || ""}/>
                        <StartButton variant={"outlined"} onClick={() => onChooseCharacter()}
                                     disabled={selectedCharacter === null}>
                            Start
                        </StartButton>
                    </>
                    : <CircularProgress/>
                }
                <CharacterToken key={`Crab`}
                                onClick={() => setSelectedCharacter(selectedCharacter === "Crab" ? null : "Crab")}
                                style={selectedCharacter === "crab" ? {borderColor: "red"} : {}}>
                    <img src={"/img/crab.png"} alt="Crab"/>
                </CharacterToken>
                {showPasswordPrompt ? <>
                        <TextField type={"password"} value={password} onChange={e => setPassword(e.target.value)}/>
                    </>
                    : null}
            </div>
            {error ?
                <Alert severity={"error"} title={"An error occured"}>{error}</Alert> : <></>
            }
        </CharacterContainer>
    </>

}