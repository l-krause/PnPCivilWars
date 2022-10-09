import {Box} from "@mui/material";

import "./token.css";

export const TOKEN_SIZE = 48;

export function Token(props) {

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

    let shadowStyle = {...style, top: 0, left: 0, position: "absolute", pointerEvents: "none"};

    if (isSelected) {
        style.border = "1px solid red";
    }

    if (character.type === "npc") {
        if (character.is_ally) {
            shadowStyle.filter = " hue-rotate(200deg)";
            style.transform = "rotate(180deg)";
            shadowStyle.transform = "rotate(180deg)";
            if (isSelected) {
                style.border = "1px solid blue";
            }
        }
    }

    let translatedPos = translatePosition(character.pos);

    return <Box className={"Token"} key={"character-" + character.id} style={{left: translatedPos.x, top: translatedPos.y}}>
        <img alt={"token of " + character.id} src={character.token}
             onDragEnd={onDrag}
             onClick={onClick}
             style={style} />
        { character.tokenShadow ?
            <img alt={"tokenShadow of " + character.id} src={character.tokenShadow} style={shadowStyle} /> :
            <></>
        }
    </Box>
}