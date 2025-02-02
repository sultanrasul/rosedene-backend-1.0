import xml.etree.ElementTree as ET
import json
import xmltodict

class Pull_GetReservationByID_RQ:
    def __init__(self, username, password, reservation_id):
        self.username = username
        self.password = password
        self.reservation_id = reservation_id


    def serialize_request(self):
        root = ET.Element("Pull_GetReservationByID_RQ")
        auth_elem = ET.SubElement(root, "Authentication")
        ET.SubElement(auth_elem, "UserName").text = self.username
        ET.SubElement(auth_elem, "Password").text = self.password
        ET.SubElement(root, "ReservationID").text = str(self.reservation_id)


        return ET.tostring(root, encoding="unicode")

    def get_details(self, response_xml):

        # Parse the response XML to a dictionary
        json_response = xmltodict.parse(response_xml)
        
        
        return json_response