import xml.etree.ElementTree as ET
import json
import xmltodict

class Push_CancelReservation_RQ:
    def __init__(self, username, password, reservation_id, cancel_type_id):
        self.username = username
        self.password = password
        self.reservation_id = reservation_id
        self.cancel_type_id = cancel_type_id

    def serialize_request(self):
        root = ET.Element("Push_CancelReservation_RQ")
        
        # Authentication block
        auth_elem = ET.SubElement(root, "Authentication")
        ET.SubElement(auth_elem, "UserName").text = self.username
        ET.SubElement(auth_elem, "Password").text = self.password

        # Reservation ID
        ET.SubElement(root, "ReservationID").text = str(self.reservation_id)

        # Cancel Type ID
        ET.SubElement(root, "CancelTypeID").text = str(self.cancel_type_id)

        return ET.tostring(root, encoding="unicode")

    def get_details(self, response_xml):

        # Parse the response XML to a dictionary
        json_response = xmltodict.parse(response_xml)
        
        
        return json_response