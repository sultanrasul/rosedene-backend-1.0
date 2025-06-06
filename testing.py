import json

testingJsonString = """

{
  "adults": 1,
  "children": 0,
  "childrenAges": [],
  "specialRequest": "testing to see if the json works in retnals united",
  "refundable": "True",
  "paymentIntentId": "pi_3RX53PAQmfY2PDog3cilLvWp",
  "country": "GB"
}
"""

bookingData = json.loads(testingJsonString)

print(bookingData["childrenAges"])
