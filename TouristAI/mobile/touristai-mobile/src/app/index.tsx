import { useState } from "react";
import LoginScreen from "../../components/login";
import NearbyExplorer from "../../components/NearbyExplorer";

export default function HomeScreen() {
  const [loggedIn, setLoggedIn] = useState(false);

  if (!loggedIn) {
    return (
      <LoginScreen
        onLogin={() => setLoggedIn(true)}
      />
    );
  }

  return <NearbyExplorer />;
}