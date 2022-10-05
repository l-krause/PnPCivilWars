import {Box} from "@mui/material";

import "./token.css";

const TOKEN_SIZE = 48;

export default function Token(props) {

    const character = props.character;
    const isSelected = !!props.isSelected;
    const onClick = props.onClick || (() => {});
    const onDrag = props.onDrag || (() => {});
    const translatePosition = props.translatePosition || (pos => pos);
    const size = props.size || TOKEN_SIZE;

    if (character.status === "dead") {
        return;
    }

    let style = {
        width: size,
        height: size,
    };

    if (isSelected) {
        style.border = "1px solid red";
    }

    if (character.type === "npc") {
        if (character.is_ally) {
            style.filter = " hue-rotate(180deg)";
        }
    }

    let translatedPos = translatePosition(character.pos);
    console.log(character.pos, "->", translatedPos);

    return <Box className={"Token"} key={"character-" + character.id} style={{left: translatedPos.x, top: translatedPos.y}}>
        <img alt={"token of " + character.id} src={character.token}
             onDragEnd={onDrag}
             onClick={onClick}
             style={style} />
    </Box>
}