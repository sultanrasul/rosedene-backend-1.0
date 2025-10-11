import xml.etree.ElementTree as ET
import json
import xmltodict
import logging

class Pull_ListPropertyAvailabilityCalendar_RQ:
    def __init__(self, username, password, property_id, date_from, date_to):
        self.username = username
        self.password = password
        self.property_id = property_id
        self.date_from = date_from
        self.date_to = date_to

    def serialize_request(self):
        root = ET.Element("Pull_ListPropertyAvailabilityCalendar_RQ")
        auth_elem = ET.SubElement(root, "Authentication")
        ET.SubElement(auth_elem, "UserName").text = self.username
        ET.SubElement(auth_elem, "Password").text = self.password
        ET.SubElement(root, "PropertyID").text = str(self.property_id)
        ET.SubElement(root, "DateFrom").text = self.date_from.strftime("%Y-%m-%d")
        ET.SubElement(root, "DateTo").text = self.date_to.strftime("%Y-%m-%d")
        return ET.tostring(root, encoding="unicode")
    
    def check_availability_calendar(self, response_xml: str) -> list:
        try:
            json_response = xmltodict.parse(response_xml)
            rs = json_response.get("Pull_ListPropertyAvailabilityCalendar_RS", {})

            # Case 3: Rentals United returned an error
            if rs.get("Status") == "Error":
                error_msg = rs.get("Error", {}).get("@Message", "Unknown error from RU")
                logging.error(f"❌ RU API error: {error_msg}")
                raise ValueError(f"RU API error: {error_msg}")

            # Case 1 & 2: Check for PropertyCalendar
            property_calendar = rs.get("PropertyCalendar")
            if not property_calendar:
                logging.warning("⚠️ No PropertyCalendar returned in response")
                return []

            calendar = property_calendar.get("CalDay")
            if not calendar:
                return []

            # Always return as list
            if isinstance(calendar, dict):
                calendar = [calendar]

            return calendar

        except Exception:
            logging.exception("Unexpected error while parsing availability calendar")
            raise

