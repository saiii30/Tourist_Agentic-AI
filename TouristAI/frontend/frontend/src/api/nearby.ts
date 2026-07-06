import axios from "axios";

export async function getNearby(lat: number, lon: number) {

    const response = await axios.get(
        "http://localhost:8000/api/nearby",
        {
            params: {
                lat,
                lon
            }
        }
    );

    return response.data;
}