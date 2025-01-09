import xml.etree.ElementTree as ET
import json
import xmltodict

class Pull_ListPropertiesBlocks_RQ:
    def __init__(self, username, password, location_id, date_from, date_to, include_nla=True):
        self.username = username
        self.password = password
        self.location_id = location_id
        self.date_from = date_from
        self.date_to = date_to
        self.include_nla = include_nla

    def serialize_request(self):
        root = ET.Element("Pull_ListPropertiesBlocks_RQ")
        auth_elem = ET.SubElement(root, "Authentication")
        ET.SubElement(auth_elem, "UserName").text = self.username
        ET.SubElement(auth_elem, "Password").text = self.password
        ET.SubElement(root, "LocationID").text = str(self.location_id)
        ET.SubElement(root, "DateFrom").text = self.date_from.strftime("%Y-%m-%d")
        ET.SubElement(root, "DateTo").text = self.date_to.strftime("%Y-%m-%d")
        ET.SubElement(root, "IncludeNLA").text = "1" if self.include_nla else "0"
        return ET.tostring(root, encoding="unicode")

    def check_blocked_properties(self, response_xml, apartment_ids):
        # Parse the response XML to a dictionary
        json_response = xmltodict.parse(response_xml)
        print(json_response)
        
        # Extract blocked properties from the response
        properties = json_response["Pull_ListPropertiesBlocks_RS"].get("Properties", None)
        if not properties:
            # If there are no blocked properties, all apartments are available
            return {
                "available": [{"id": apartment_id, "name": apartment_name} for apartment_id, apartment_name in apartment_ids.items()],
                "blocked": []
            }

        # Extract the IDs of blocked properties
        blocked_ids = set()
        if "PropertyBlock" in properties:
            if isinstance(properties["PropertyBlock"], list):
                # Multiple blocked properties
                blocked_ids = {int(property_block["@PropertyID"]) for property_block in properties["PropertyBlock"]}
            else:
                # Single blocked property
                blocked_ids = {int(properties["PropertyBlock"]["@PropertyID"])}
        else:
            # If "PropertyBlock" key is not present, assume no blocked properties
            return {
                "available": [{"id": apartment_id, "name": apartment_name} for apartment_id, apartment_name in apartment_ids.items()],
                "blocked": []
            }

        # Find available properties by subtracting blocked IDs from all apartment IDs
        available_ids = set(apartment_ids.keys()) - blocked_ids

        # Map IDs to dictionaries containing both ID and name for available and blocked properties
        available = [{"id": apartment_id, "name": apartment_ids[apartment_id]} for apartment_id in available_ids]
        blocked = [{"id": apartment_id, "name": apartment_ids[apartment_id]} for apartment_id in blocked_ids if apartment_id in apartment_ids]

        return {
            "available": available,
            "blocked": blocked
        }
