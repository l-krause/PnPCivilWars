import {Box, styled} from "@mui/material";

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

export default CharacterToken;