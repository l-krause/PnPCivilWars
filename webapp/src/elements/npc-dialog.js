import {
    Box,
    Checkbox,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle, FormControlLabel,
    TextField
} from "@mui/material";
import Button from "@mui/material/Button";
import {useState} from "react";

import "./dialogs.css"

export default function NpcDialog(props) {
    let npcDialog = props.npcDialog;
    let setNpcDialog = props.setNpcDialog;
    let api = props.api;

    const [npcAmount, setNPCAmount] = useState(20);
    const [npcAlly, setNPCAlly] = useState(true);

    const addNpcs = () => {
        let data = {"allies": npcAlly, "amount": npcAmount}
        api.sendRequest("createNPCs", data, (response) => {
            if (!response.success) {
                alert(response.msg);
            }
        })
    };

    return <Dialog open={npcDialog} onClose={() => setNpcDialog(false)}>
        <DialogTitle>Create NPCs</DialogTitle>
        <DialogContent>
            <DialogContentText>
                Choose how many NPCs to create and if they should be created as allies.
            </DialogContentText>
            <Box mt={2}>
                <TextField type={"number"} inputProps={{ min: 1 }} label="Amount" value={npcAmount}
                           size={"small"}
                           onChange={e => setNPCAmount(parseInt(e.target.value))}/>
                <FormControlLabel  label={"Spawn Allys?"} className={"checkbox-ally"}
                    control={<Checkbox label={"chk_ally?"} checked={npcAlly} onChange={() => setNPCAlly(!npcAlly)}/>} />
            </Box>
        </DialogContent>
        <DialogActions>
            <Button variant={"outlined"} onClick={() => {
                addNpcs();
                setNpcDialog(false);
            }}>Create</Button>
            <Button variant={"outlined"} onClick={() => setNpcDialog(false)}>Cancel</Button>
        </DialogActions>
    </Dialog>
}