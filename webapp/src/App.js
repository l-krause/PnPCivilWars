import manollo from './assets/manollo.png';
import thork from './assets/thork.png';
import bmap from './assets/battlemap.png';
import './App.css';
import {useState} from "react";


export function BattleMap(props) {
    return (
        <div className="App">
            <img src={bmap} className="BattleMap" alt="BattleMap"/>
        </div>
    )
}


export function CharacterSelection(props) {

    return (
        <div className="App">
            <b>Choose your character first!</b>
            <div className="Chooser">
                <img src={manollo} className="Manollo" alt="Manollo" onClick={(c) => props.onChooseCharacter("1")}/>
                <img src={thork} className="Thork" alt="Thork" onClick={(c) => props.onChooseCharacter("2")}/>
                <img src={manollo} className="Manollo" alt="Manollo" onClick={(c) => props.onChooseCharacter("3")}/>
                <img src={thork} className="Thork" alt="Thork" onClick={(c) => props.onChooseCharacter("4")}/>
            </div>
        </div>
    )
}


function App() {
    const [character, setCharacter] = useState(null);
    console.log(character)
    if (character) {
        return (
            <BattleMap char={character}/>
        );
    } else {
        return (<CharacterSelection onChooseCharacter={(c) => setCharacter(c)} />)
    }

}

export default App;
