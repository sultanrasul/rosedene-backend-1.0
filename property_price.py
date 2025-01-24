import xml.etree.ElementTree as ET
import xmltodict
import requests
from datetime import datetime

class Pull_ListPropertyPrices_RQ:
    def __init__(self, username, password, property_id, date_from, date_to, api_endpoint):
        self.username = username
        self.password = password
        self.property_id = property_id
        self.date_from = date_from
        self.date_to = date_to
        self.api_endpoint = api_endpoint

    def serialize_request(self):
        root = ET.Element("Pull_ListPropertyPrices_RQ")
        auth_elem = ET.SubElement(root, "Authentication")
        ET.SubElement(auth_elem, "UserName").text = self.username
        ET.SubElement(auth_elem, "Password").text = self.password
        ET.SubElement(root, "PropertyID").text = str(self.property_id)
        ET.SubElement(root, "DateFrom").text = self.date_from.strftime("%Y-%m-%d")
        ET.SubElement(root, "DateTo").text = self.date_to.strftime("%Y-%m-%d")
        return ET.tostring(root, encoding="unicode")

    def get_price(self, response_xml):
        json_response = xmltodict.parse(response_xml)
        price = json_response.get("Pull_ListPropertyPrices_RS", {})
        return price

    @staticmethod
    def get_prices_for_multiple_properties(username, password, property_ids, date_from, date_to, api_endpoint):
        prices = []

        for property_id in property_ids:
            request = Pull_ListPropertyPrices_RQ(username, password, property_id, date_from, date_to, api_endpoint)
            serialized_request = request.serialize_request()

            # Make the API request
            response = requests.post(api_endpoint, data=serialized_request, headers={"Content-Type": "application/xml"})
            
            if response.status_code == 200:
                # Process the XML response
                response_xml = response.text
                price = request.get_price(response_xml)
                prices.append({"property_id": property_id, "price": price})
            else:
                print(f"Error fetching price for property {property_id}: {response.status_code}")
        
        return prices