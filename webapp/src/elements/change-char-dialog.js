import {Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, TextField} from "@mui/material";
import Button from "@mui/material/Button";
import {useState} from "react";

import "./dialogs.css"

export default function ChangeCharDialog(props) {
    let changeChar = props.changeChar;
    let setChangeChar = props.setChangeChar;
    let selectedCharacter = props.selectedCharacter;
    let api = props.api;
    const [changeHp, setChangeHp] = useState(0);
    const [changeMaxHp, setChangeMaxHp] = useState(0);
    const [changeDamage, setChangeDamage] = useState(0);
    const [changeAdd, setChangeAdd] = useState(0);
    const [changeArmor, setChangeArmor] = useState(0);
    const [changeDice, setChangeDice] = useState(0);

    const changeSelCharacter = () => {
        let data = {
            "character": selectedCharacter,
            "curr_hp": changeHp,
            "max_hp": changeMaxHp,
            "dice": changeDice,
            "damage": changeDamage,
            "modifier": changeAdd,
            "armor": changeArmor
        }
        api.sendRequest("changeSelChar", data, (response) => {
            if (response.success) {
                setChangeChar(false);
            } else {
                alert(response.msg);
            }
        })
    }

    return <Dialog open={changeChar} onClose={() => setChangeChar(false)}>
        <DialogTitle>Create NPCs</DialogTitle>
        <DialogContent className={"dialog-content"}>
            <DialogContentText>
                Choose how you want to modify the character
            </DialogContentText>
            <TextField size={"small"} label="Max HP" value={changeMaxHp} onChange={e => setChangeMaxHp(e.target.value)}/>
            <TextField size={"small"} label="Curr_HP" value={changeHp} onChange={e => setChangeHp(e.target.value)}/>
            <TextField size={"small"} label="Damage Dice" value={changeDice} onChange={e => setChangeDice(e.target.value)}/>
            <TextField size={"small"} label="Dice Type" value={changeDamage} onChange={e => setChangeDamage(e.target.value)}/>
            <TextField size={"small"} label="Damage Additional" value={changeAdd} onChange={e => setChangeAdd(e.target.value)}/>
            <TextField size={"small"} label="Armor" value={changeArmor} onChange={e => setChangeArmor(e.target.value)}/>
        </DialogContent>
        <DialogActions>
            <Button variant={"outlined"} onClick={() => {
                changeSelCharacter();
            }}>Change</Button>
            <Button variant={"outlined"} onClick={() => setChangeChar(false)}>Cancel</Button>
        </DialogActions>
    </Dialog>
}