from bs4 import BeautifulSoup

with open("worker/logs/screenshots/sherly_chat_html.txt", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find the main direct message container
messages = soup.find_all(string=lambda text: "basics" in text.lower() if text else False)
print("Found texts with 'basics':")
for msg in messages:
    print(msg.strip())

# Let's print all text in the main messaging area
chat_div = soup.find('div', {'role': 'presentation'})
if chat_div:
    print("\nChat div found!")

# Try to find all message bubbles based on typical Instagram DOM
# Often messages are inside divs with specific data attributes or classes
for div in soup.find_all('div', dir='auto'):
    text = div.get_text()
    if len(text) > 5 and len(text) < 100:
        print(f"Potential msg: {text}")
