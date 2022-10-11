import "./dialogs.css"
import {useState} from "react";
import {
    Box, Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    TextField
} from "@mui/material";
import Button from "@mui/material/Button";

export default function ChangeHealthDialog(props) {
    let api = props.api;
    let character = props.character;
    let changeHpDialog = props.changeHpDialog;
    let setChangeHpDialog = props.setChangeHpDialog;
    const [hp, setHp] = useState(0)

    return <Dialog open={changeHpDialog} onClose={() => setChangeHpDialog(false)}>
        <DialogTitle>Change HPs</DialogTitle>
        <DialogContent>
            <DialogContentText>
                Choose the number by which the selected characters HP should be changed.
            </DialogContentText>
            <Box mt={2}>
                <TextField type={"number"} label="Amount" value={hp}
                           size={"small"}
                           onChange={e => setHp(parseInt(e.target.value))}/>
            </Box>
        </DialogContent>
        <DialogActions>
            <Button variant={"outlined"} onClick={() => {
                let data = {"target": character, "life": hp}
                api.sendRequest("changeHealth", data)
                setChangeHpDialog(false)
            }}>Change</Button>
            <Button variant={"outlined"} onClick={() => setChangeHpDialog(false)}>Cancel</Button>
        </DialogActions>
    </Dialog>

}