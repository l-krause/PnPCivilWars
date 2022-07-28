import {useCallback, useEffect, useMemo, useState} from "react";
import CharacterSelection from "./views/character-selection";
import {Alert, AlertTitle, Box, Button, CircularProgress, styled} from "@mui/material";
import ReplayIcon from '@mui/icons-material/Replay';
import API from "./api";
import BattleMap from "./views/battlemap";


const ConnectingDialog = styled(Box)(({theme }) => ({
  textAlign: "center",
  marginTop: theme.spacing(4)
}));

const ConnectionError = styled(Box)(({theme}) => ({
  maxWidth: 800,
  marginLeft: "auto",
  marginRight: "auto",
  textAlign: "left",
  "& button": {
    marginTop: theme.spacing(1)
  }
}));

function App() {

  const api = useMemo(() => new API(), []);
  const [character, setCharacter] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsError, setWsError] = useState(null);
  const [loaded, setLoaded] = useState(false);

  const onConnect = useCallback(() => {
    console.log('SocketIO Client Connected');
    setWsConnected(true);
  }, []);

  const onDisconnect = useCallback(() => {
    console.log('SocketIO Client closed');
    setWsConnected(false);
  }, []);

  const onError = useCallback((err) => {
    console.log('err', err);
    setWsConnected(false);
    setWsError(err);
  }, []);

  useEffect(() => {
    if (!loaded && wsConnected) {
      api.info((response) => {
        if (response.success) {
          setLoaded(true);
          setCharacter(response.data.player.character);
        } else {
          setWsConnected(false);
          setWsError("Error fetching character info: " + response.msg);
        }
      });
    }
  }, [api, loaded, wsConnected]);

  useEffect(() => {
    if (!wsConnected && !wsError) {
      console.log("api.reconnect()");
      const io = api.reconnect();
      io.on("error", onError);
      io.on("connect", onConnect);
      io.on("disconnect", onDisconnect);
    }
  }, [wsConnected, wsError, api, onDisconnect, onError, onConnect]);

  return <div className="App">
    {wsConnected ?
        (loaded ?
          (character !== null ?
                  <BattleMap api={api} character={character}/> :
                  <CharacterSelection api={api} onSelectCharacter={(c) => setCharacter(c)}/>
          ) :
            <ConnectingDialog>
              <div>Loading...</div>
              <CircularProgress size={25} />
            </ConnectingDialog>) :
        <ConnectingDialog>
          {wsError ?
              <ConnectionError>
                <Alert severity="error">
                  <AlertTitle>Error establishing WebSocket connection</AlertTitle>
                  <div>{ api.getErrorMessage(wsError.code) }</div>
                  <Button size={"small"} variant={"outlined"} color={"error"}>
                    <ReplayIcon fontSize={"small"} onClick={() => setWsError(null)} />&nbsp;Retry
                  </Button>
                </Alert>
              </ConnectionError>
              :
              <>
                <div>Connecting to Server...</div>
                <CircularProgress size={25} />
              </>
          }
        </ConnectingDialog>
    }
  </div>
}

export default App;
