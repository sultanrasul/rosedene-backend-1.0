import xml.etree.ElementTree as ET
import xmltodict
import requests
import json
import os
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
    def get_prices_for_multiple_properties_save_to_file(
        username, password, property_ids, date_from, date_to, api_endpoint, file_path="property_prices.json"
    ):
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

        # Save the data to a file
        with open(file_path, "w") as file:
            json.dump(prices, file, indent=4)

        print(f"Prices successfully saved to {file_path}")
        return prices

    @staticmethod
    def get_all_prices(file_path="property_prices.json"):
        # Check if the file exists
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                saved_prices = json.load(file)
            return saved_prices
        else:
            print(f"No saved prices found in {file_path}. Please call 'get_prices_for_multiple_properties_save_to_file' first.")
            return []
        
    @staticmethod
    def get_prices_for_property(property_id, file_path="property_prices.json"):
        """
        Get price data for a specific property ID from a JSON file.
    
        :param property_id: The ID of the property to fetch prices for.
        :param file_path: The path to the JSON file containing property prices.
        :return: The price data for the given property ID, or None if not found.
        """
        # Check if the file exists
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                saved_prices = json.load(file)
            
            # Find the property with the matching ID
            property_data = next((p for p in saved_prices if p.get("property_id") == property_id), None)
            if property_data:
                return property_data
            else:
                print(f"No data found for property ID: {property_id}.")
                return None
        else:
            print(f"No saved prices found in {file_path}. Please call 'get_prices_for_multiple_properties_save_to_file' first.")
            return None
        
    @staticmethod
    def calculate_price(property_id, nights, guests):
        price = Pull_ListPropertyPrices_RQ.get_prices_for_property(property_id=property_id)
        dailyPrice = float(price["price"]["Prices"]["Season"]["Price"])
        extra = float(price["price"]["Prices"]["Season"]["Extra"])
        print(dailyPrice,extra)
        
        basePrice = (dailyPrice * int(nights)) + extra
        if (int(guests) > 2):
            basePrice += (int(guests)-2) * extra       

        print(basePrice)
        return basePrice

