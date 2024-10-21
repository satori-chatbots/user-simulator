import wit
import duckling

access_token = '32ZBGUAAVSV5SINUIYYAUSCV4HLSV2YU'
client = wit.Wit(access_token)

# capturing numeric entity using raw text(example0) using wit.ai client instance
example0 = "I want to read 3 geekforgeeks articles."
response = client.message(example0)
print(response)
