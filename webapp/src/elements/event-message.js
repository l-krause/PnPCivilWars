import "./event-message.css"

export default function EventMessage(props) {
    let message = props.eventMessage;
    let color = props.color;

    return <div>
        <p>{message}</p>
    </div>;
}