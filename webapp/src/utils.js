

const getBaseUrl = () => {
    /*if (typeof process !== 'undefined' && (!process.env.NODE_ENV || process.env.NODE_ENV === 'development')) {
        return "localhost:3000/ws";
    } else {
        return "dnd.romanh.de/ws";
    }*/

    return "wss://dnd.romanh.de/ws";
}

module.exports = { getBaseUrl };