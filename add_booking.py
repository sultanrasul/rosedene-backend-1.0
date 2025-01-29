import xml.etree.ElementTree as ET
from typing import List, Optional
import xmltodict

class Push_PutConfirmedReservationMulti_RQ:
    def __init__(self, username, password, property_id, date_from, date_to, number_of_guests,ru_price, client_price,
                 already_paid, customer_name, customer_surname, customer_email, customer_phone, customer_zip_code,
                 number_of_adults, commission, number_of_children, children_ages: Optional[List[int]], comments: Optional[str] = None):
        self.username = username
        self.password = password
        self.property_id = property_id
        self.date_from = date_from
        self.date_to = date_to
        self.number_of_guests = number_of_guests
        self.ru_price = ru_price
        self.client_price = client_price
        self.already_paid = already_paid
        self.customer_name = customer_name
        self.customer_surname = customer_surname
        self.customer_email = customer_email
        self.customer_phone = customer_phone
        self.customer_zip_code = customer_zip_code
        self.number_of_adults = number_of_adults
        self.number_of_children = number_of_children
        self.children_ages = children_ages if children_ages is not None else []
        self.comments = comments
        self.commission = commission
    

    def serialize_request(self):
        root = ET.Element("Push_PutConfirmedReservationMulti_RQ")
        
        # Authentication Element
        auth_elem = ET.SubElement(root, "Authentication")
        ET.SubElement(auth_elem, "UserName").text = self.username
        ET.SubElement(auth_elem, "Password").text = self.password
        
        # Reservation Element
        reservation_elem = ET.SubElement(root, "Reservation")
        
        # StayInfos Element
        stayinfos_elem = ET.SubElement(reservation_elem, "StayInfos")
        stayinfo_elem = ET.SubElement(stayinfos_elem, "StayInfo")
        ET.SubElement(stayinfo_elem, "PropertyID").text = str(self.property_id)
        ET.SubElement(stayinfo_elem, "DateFrom").text = self.date_from.strftime("%Y-%m-%d")
        ET.SubElement(stayinfo_elem, "DateTo").text = self.date_to.strftime("%Y-%m-%d")
        ET.SubElement(stayinfo_elem, "NumberOfGuests").text = str(self.number_of_guests)
        
        # Costs Element
        costs_elem = ET.SubElement(stayinfo_elem, "Costs")
        ET.SubElement(costs_elem, "RUPrice").text = str(self.ru_price)
        ET.SubElement(costs_elem, "ClientPrice").text = str(self.client_price)
        ET.SubElement(costs_elem, "AlreadyPaid").text = str(self.already_paid)
        ET.SubElement(costs_elem, "ChannelCommission").text = str(self.commission)
        
        # CustomerInfo Element
        customer_info_elem = ET.SubElement(reservation_elem, "CustomerInfo")
        ET.SubElement(customer_info_elem, "Name").text = self.customer_name
        ET.SubElement(customer_info_elem, "SurName").text = self.customer_surname
        ET.SubElement(customer_info_elem, "Email").text = self.customer_email
        ET.SubElement(customer_info_elem, "Phone").text = self.customer_phone
        ET.SubElement(customer_info_elem, "ZipCode").text = self.customer_zip_code
        
        # GuestDetailsInfo Element
        guest_details_elem = ET.SubElement(reservation_elem, "GuestDetailsInfo")
        ET.SubElement(guest_details_elem, "NumberOfAdults").text = str(self.number_of_adults)
        ET.SubElement(guest_details_elem, "NumberOfChildren").text = str(self.number_of_children)
        
        # Only add ChildrenAges if there are children
        if self.number_of_children > 0 and self.children_ages:
            children_ages_elem = ET.SubElement(guest_details_elem, "ChildrenAges")
            for age in self.children_ages:
                ET.SubElement(children_ages_elem, "Age").text = str(age)
        
        # Add Comments element only if a comment is provided
        if self.comments:
            ET.SubElement(reservation_elem, "Comments").text = self.comments
        
        return ET.tostring(root, encoding="unicode")
    
    def booking_reference(self, response_xml):
        json_response = xmltodict.parse(response_xml)
        calendar = json_response["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]
        return calendar
