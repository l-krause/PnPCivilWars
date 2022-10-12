import {useState} from "react";
import {
    Box,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle, MenuItem,
    Select
} from "@mui/material";
import Button from "@mui/material/Button";

export default function SwitchWeaponDialog(props){
    let api = props.api;
    let switchWeaponDialog = props.switchWeaponDialog;
    let setSwitchWeaponDialog = props.setSwitchWeaponDialog;
    let activeWeapon = props.activeWeapon;
    let weapons = props.weapons;

    const [switchWeapon, setSwitchWeapon] = useState(activeWeapon);

    let weaponsDropDown = Object.values(weapons).map(w => <MenuItem value={w}>{w}</MenuItem>)


    return <Dialog open={switchWeaponDialog} onClose={() => setSwitchWeaponDialog(false)}>
        <DialogTitle>Change HPs</DialogTitle>
        <DialogContent>
            <DialogContentText>
                Choose your weapon! Current active weapon: {activeWeapon}
            </DialogContentText>
            <Box mt={2}>
                <Select value={switchWeapon} onChange={(e) => setSwitchWeapon(e.target.value)}>
                    {weaponsDropDown}
                </Select>
            </Box>
        </DialogContent>
        <DialogActions>
            <Button variant={"outlined"} onClick={() => {
                let data = {"name": switchWeapon}
                api.sendRequest("switchWeapon", data)
                setSwitchWeaponDialog(false)
            }}>Change</Button>
            <Button variant={"outlined"} onClick={() => setSwitchWeaponDialog(false)}>Cancel</Button>
        </DialogActions>
    </Dialog>
}