import xml.etree.ElementTree as ET
import xmltodict
import requests
import json
import os
from datetime import datetime, timedelta


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
    def get_prices_for_multiple_properties_save_to_file(username, password, property_ids, date_from, date_to, api_endpoint, file_path="property_prices.json"):
        prices_dict = {}

        for property_id in property_ids:
            request = Pull_ListPropertyPrices_RQ(username, password, property_id, date_from, date_to, api_endpoint)
            serialized_request = request.serialize_request()

            # Make the API request
            response = requests.post(api_endpoint, data=serialized_request, headers={"Content-Type": "application/xml"})

            if response.status_code == 200:
                # Process the XML response
                response_xml = response.text
                price = request.get_price(response_xml)
                prices_dict[property_id] = price  # Store price with property_id as the key
            else:
                print(f"Error fetching price for property {property_id}: {response.status_code}")

        # Save the data to a file
        with open(file_path, "w") as file:
            json.dump(prices_dict, file, indent=4)

        print(f"Prices successfully saved to {file_path}")
        return prices_dict


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
    
    # @staticmethod
    # def calculate_ru_price(property_id, nights, guests):
    #     price = Pull_ListPropertyPrices_RQ.get_all_prices()[str(property_id)]
    #     dailyPrice = float(price["price"]["Prices"]["Season"]["Price"])
    #     extra = float(price["price"]["Prices"]["Season"]["Extra"])
        
    #     basePrice = (dailyPrice * int(nights))
    #     if (int(guests) > 2):
    #         basePrice += (int(guests)-2) * extra * nights       

    #     return basePrice

    @staticmethod
    def calculate_ru_price(property_id, guests, date_from, date_to):
        saved_prices = Pull_ListPropertyPrices_RQ.get_all_prices()
        
        property_data = saved_prices[str(property_id)]
        prices_info = property_data["Prices"]

        if "Season" not in prices_info:
            print(f"No seasonal pricing available for property ID {str(property_id)}.")
            return None
        
        if not isinstance(prices_info["Season"], list):
                prices_info["Season"] = [prices_info["Season"]]

        total_price = 0
        current_date = date_from

        # Iterate over each night in the stay
        while current_date < date_to:
            for season in prices_info["Season"]:
                season_start = datetime.strptime(season["@DateFrom"], "%Y-%m-%d")
                season_end = datetime.strptime(season["@DateTo"], "%Y-%m-%d")

                # If the current night falls within a season range, add its price
                if season_start <= current_date <= season_end:
                    total_price += float(season["Price"])
                    if (guests > 2):
                        total_price += float(season["Extra"]) * (guests - 2)
                    
                    break  # No need to check other seasons for the same night
            
            current_date += timedelta(days=1)  # Move to next night

        return total_price

    @staticmethod
    def calculate_refundable_rate_fee(total_price):
        total_price = float(total_price)  # Convert to float
        refundableRate = round(total_price * 0.0575, 2) # times by 5.75% for the refundable rate

        return refundableRate

    @staticmethod
    def calculate_client_price(basePrice,  refundable):

        if refundable:
            refundableRateFee = Pull_ListPropertyPrices_RQ.calculate_refundable_rate_fee(basePrice)
            basePrice+=refundableRateFee
            
        return basePrice
    

