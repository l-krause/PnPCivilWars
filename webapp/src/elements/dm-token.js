import CharacterToken from "./character-token";
import {Box, styled} from "@mui/material";

const DMText = styled(Box)(({theme}) => ({
    fontSize: 30,
    fontWeight: "bold",
    color: "red",
    padding: theme.spacing(3)
}));

export default function DMToken(props) {

    const onClick = props.onClick || (() => {});
    const isSelected = !!props.isSelected;

    return <CharacterToken key={`character-crab`} onClick={onClick}
                sx={isSelected ? {borderColor: "red"} : {}}>
                <DMText>DM</DMText>
            </CharacterToken>
}