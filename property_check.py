import xml.etree.ElementTree as ET
import json
import xmltodict

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

    def check_availability_calendar(self, response_xml):
        json_response = xmltodict.parse(response_xml)
        calendar = json_response["Pull_ListPropertyAvailabilityCalendar_RS"]["PropertyCalendar"]["CalDay"]
        return calendar
