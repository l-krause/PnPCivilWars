import {Checkbox, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, TextField} from "@mui/material";
import Button from "@mui/material/Button";
import {useState} from "react";

export default function NpcDialog(props) {
    let npcDialog = props.npcDialog;
    let setNpcDialog = props.setNpcDialog;
    let api = props.api;

    const [npcAmount, setNPCAmount] = useState(20);
    const [npcAlly, setNPCAlly] = useState(true);

    const addNpcs = () => {
        let data = {"allies": npcAlly, "amount": parseInt(npcAmount + "")}
        api.sendRequest("createNPCs", data)
    };

    return <Dialog open={npcDialog} onClose={() => setNpcDialog(false)}>
        <DialogTitle>Create NPCs</DialogTitle>
        <DialogContent>
            <DialogContentText>
                Choose how many NPCs to create and if they should be created as allies.
            </DialogContentText>
            <TextField label="Amount" value={npcAmount} onChange={e => setNPCAmount(e.target.value)}/>
            <Checkbox label={"Ally?"} checked={npcAlly} onChange={() => setNPCAlly(!npcAlly)}/>
        </DialogContent>
        <DialogActions>
            <Button onClick={() => {
                addNpcs();
                setNpcDialog(false);
            }}>Create</Button>
            <Button onClick={() => setNpcDialog(false)}>Cancel</Button>
        </DialogActions>
    </Dialog>
}