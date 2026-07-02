from typing import List

class EmergencyService:
    @staticmethod
    def get_emergency_contacts(city: str) -> List[dict]:
        city_clean = city.strip().lower()
        
        # Base generic contacts for India
        contacts = [
            {"role": "National Emergency Helpline", "number": "112", "location": "Toll-free emergency help"},
            {"role": "Police Control Room", "number": "100", "location": "Local Police Station"},
            {"role": "Ambulance Services", "number": "108", "location": "Medical Emergency Support"}
        ]
        
        # Localized contacts
        if "madurai" in city_clean:
            contacts.append({"role": "Apollo Hospital Madurai", "number": "+91 452 253 1044", "location": "Lake View Road, Madurai"})
            contacts.append({"role": "Tourist Information Counter", "number": "+91 452 233 4757", "location": "Railway Junction Station"})
        elif "goa" in city_clean:
            contacts.append({"role": "Manipal Hospital Goa", "number": "+91 832 304 8800", "location": "Dona Paula, Panaji"})
            contacts.append({"role": "Goa Tourism Helpdesk", "number": "1364", "location": "Paryatan Bhavan, Panaji"})
        elif "chennai" in city_clean:
            contacts.append({"role": "Apollo Hospital Greams Road", "number": "+91 44 2829 0200", "location": "Greams Lane, Chennai"})
            contacts.append({"role": "Chennai Tourist Office", "number": "+91 44 2538 0583", "location": "Central Railway Station"})
        elif "ooty" in city_clean:
            contacts.append({"role": "Ooty Government Hospital", "number": "+91 423 244 2200", "location": "Hospital Road, Ooty"})
            contacts.append({"role": "Nilgiris District Tourist Office", "number": "+91 423 244 3977", "location": "Charring Cross, Ooty"})
        else:
            contacts.append({"role": "Local Tourist Police Helpline", "number": "1090", "location": "General tourist safety desk"})
            
        return contacts
