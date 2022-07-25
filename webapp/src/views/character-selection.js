import {useCallback, useEffect, useState} from "react";

export default function CharacterSelection(props) {

    const onSelectCharacter = props.onSelectCharacter;
    const api = props.api;

    const [characters, setCharacters] = useState(null);
    const [fetchCharacters, setFetchCharacters] = useState(true);

    const onFetchCharacters = useCallback((force = false) => {
        api.getCharacters((data) => {

        });
    }, [api]);

    const onRequestCharacter = useCallback((c) => {

    }, []);

    useEffect(() => {
        if (characters === null || fetchCharacters) {
            onFetchCharacters();
        }
    }, [fetchCharacters, characters, onFetchCharacters]);

    return <>
        <b>Choose your character first!</b>
        <div className="Chooser">

        </div>
    </>

}