import requests


url = "http://127.0.0.1:8000/update"

response = requests.get(url)

if response.status_code == 200:
    with open("downloaded_hello.txt", "wb") as file:
        file.write(response.content)
    print("download successful")
else:
    print(f"error, status: {response.status_code}")
