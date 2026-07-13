import { useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";

import * as Location from "expo-location";
import { Magnetometer } from "expo-sensors";
import * as Speech from "expo-speech";
import * as Linking from "expo-linking";

import { api } from "../services/api";

// type Place = {
//   name: string;
//   lat: number;
//   lon: number;
//   distance: number;
// };

type Place = {
  name: string;
  lat: number;
  lon: number;
  rating: number;
  category: string;
  address: string;
};

export default function NearbyExplorer() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [heading, setHeading] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // useEffect(() => {
  //   loadLocation();

  //   Magnetometer.setUpdateInterval(300);

  //   const subscription = Magnetometer.addListener((data) => {
  //     const angle = Math.atan2(data.y, data.x);
  //     const degree = angle * (180 / Math.PI);

  //     setHeading((degree + 360) % 360);
  //   });

  //   return () => {
  //     subscription.remove();
  //   };
  // }, []);

useEffect(() => {

  loadLocation();

  const interval = setInterval(() => {
    loadLocation();
  }, 5000);

  Magnetometer.setUpdateInterval(300);

  const subscription = Magnetometer.addListener((data) => {
    const angle = Math.atan2(data.y, data.x);
    const degree = angle * (180 / Math.PI);

    setHeading((degree + 360) % 360);
  });

  return () => {
    clearInterval(interval);
    subscription.remove();
  };

}, []);



  // const loadLocation = async () => {
  //   try {
  //     console.log("========== LOCATION DEBUG ==========");

  //     const enabled = await Location.hasServicesEnabledAsync();
  //     console.log("GPS Enabled:", enabled);

  //     if (!enabled) {
  //       setError("Location Services are OFF");
  //       setLoading(false);
  //       return;
  //     }

  //     const permission =
  //       await Location.requestForegroundPermissionsAsync();

  //     console.log("Permission:", permission.status);

  //     if (permission.status !== "granted") {
  //       setError("Location permission denied");
  //       setLoading(false);
  //       return;
  //     }

  //     const last =
  //       await Location.getLastKnownPositionAsync();

  //     console.log("Last Known:", last);

  //     console.log("Getting Current Position...");

  //     const location =
  //       await Location.getCurrentPositionAsync({
  //         accuracy: Location.Accuracy.Highest,
  //       });

  //     console.log("Current Location:", location.coords);

  //     const response = await api.get("/api/nearby", {
  //       params: {
  //         lat: location.coords.latitude,
  //         lon: location.coords.longitude,
  //       },
  //     });

  //     console.log("Nearby Response");
  //     console.log(response.data);

  //     setPlaces(response.data);

  //     setLoading(false);
  //   } catch (err) {
  //     console.log("LOCATION ERROR");
  //     console.log(err);

  //     setError("Unable to fetch current location.");
  //     setLoading(false);
  //   }
  // };


  const loadLocation = async () => {
  try {
    setLoading(true);
    setError("");

    console.log("========== LOCATION DEBUG ==========");

    // Check if GPS is enabled
    const enabled = await Location.hasServicesEnabledAsync();
    console.log("GPS Enabled:", enabled);

    if (!enabled) {
      setError("Location Services are OFF");
      setLoading(false);
      return;
    }

    // Request permission
    const permission =
      await Location.requestForegroundPermissionsAsync();

    console.log("Permission:", permission.status);

    if (permission.status !== "granted") {
      setError("Location permission denied");
      setLoading(false);
      return;
    }

    // Get last known location (optional, for debugging)
    const last = await Location.getLastKnownPositionAsync();

    console.log("Last Known:", last);

    console.log("Getting Current Position...");

    // Get current GPS location
    const location = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.High,
    });

    console.log("Current Location:");
    console.log(location.coords);

    // -----------------------------
    // Call your FastAPI backend
    // -----------------------------
    const response = await api.get("/api/nearby", {
      params: {
        lat: location.coords.latitude,
        lon: location.coords.longitude,
      },
    });

    console.log("Nearby Response:");
    console.log(response.data);

    setPlaces(response.data);

    setLoading(false);

  } catch (err) {
    console.log("LOCATION ERROR");
    console.log(err);

    setError("Unable to fetch current location.");
    setLoading(false);
  }
};

  const speakPlace = (name: string) => {
    Speech.speak(`Welcome to ${name}`);
  };

  const openMaps = (lat: number, lon: number) => {
    Linking.openURL(
      `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 15 }}>
          Detecting your location...
        </Text>
      </View>
    );
  }

  if (error !== "") {
    return (
      <View style={styles.center}>
        <Text style={{ color: "red", fontSize: 16 }}>
          {error}
        </Text>

        <TouchableOpacity
          style={styles.retry}
          onPress={loadLocation}
        >
          <Text style={{ color: "#fff" }}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🧭 Nearby Explorer</Text>

      <Text style={styles.heading}>
        Heading : {Math.round(heading)}°
      </Text>

      <FlatList
        data={places}
        keyExtractor={(item) => item.name}
        ListEmptyComponent={() => (
          <Text style={{ marginTop: 50 }}>
            No nearby attractions found.
          </Text>
        )}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.place}>
              {item.name}
            </Text>

            {/* <Text>
              {item.distance?.toFixed(2)} km
            </Text> */}
<Text>{item.category}</Text>

<Text>{item.address}</Text>

<Text>⭐ {item.rating}</Text>
            <TouchableOpacity
              onPress={() => speakPlace(item.name)}
            >
              <Text style={styles.blue}>
                🔊 Whisper
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() =>
                openMaps(item.lat, item.lon)
              }
            >
              <Text style={styles.green}>
                Directions
              </Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#F5F7FA",
  },

  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },

  title: {
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 15,
  },

  heading: {
    marginBottom: 20,
    fontSize: 16,
  },

  retry: {
    marginTop: 20,
    backgroundColor: "#2196F3",
    paddingHorizontal: 25,
    paddingVertical: 10,
    borderRadius: 8,
  },

  card: {
    backgroundColor: "white",
    padding: 15,
    borderRadius: 12,
    marginBottom: 12,
    elevation: 3,
  },

  place: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 5,
  },

  blue: {
    color: "#0066ff",
    marginTop: 12,
    fontWeight: "600",
  },

  green: {
    color: "green",
    marginTop: 10,
    fontWeight: "600",
  },
});