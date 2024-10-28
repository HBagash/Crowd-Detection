export class PassengerDataApi {
    public static async getData() {
        const response = await fetch("https://gist.githubusercontent.com/ashraf7772/b3cc3c047f38bafd22e5ac9ce2ea429e/raw/3721479c8063f84dd688d903b1c87e7695d30c52/airport.json"); 

        
        const deviceData = response.json(); 

        return deviceData;
    }
}