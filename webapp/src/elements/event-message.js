import "./event-message.css"

export default function EventMessage(props) {
    let message = props.eventMessage;
    let textColor = props.color;

    let style = {
        position: "relative",
        color: textColor
    }

    return <div style={style}>
        {message}
    </div>;
}