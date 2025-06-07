#y4WFaNEhRxzqcRwfgKRgVsNbiQDCMeFL
#2b10Vl5dhLICHWdan4u52n1NWe

import os
import requests
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, session, render_template, jsonify
from flask_mail import Mail, Message  # Ensure this line is present
import random


app = Flask(__name__, static_folder="static")

# 🔹 Set API Keys
MISTRAL_API_KEY = "y4WFaNEhRxzqcRwfgKRgVsNbiQDCMeFL"  # ⬅️ Replace with your actual key
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# 🔹 API Keys
PLANTNET_API_KEY = "2b10f6XyLbRzUMmomxn3cZjMO"
AUTH_TOKEN = "2b10UJhFQMXNClo0grqgVCO"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

@app.route("/")
def home():
    return render_template("index.html")


# ✅ Handle Text-Based Queries (Mistral AI)
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_question = data.get("question", "")

    if not user_question:
        return jsonify({"error": "Please enter a question"}), 400

    try:
        payload = {
            "model": "mistral-medium",
            "messages": [
                {"role": "system", "content": "You are an expert in farming. Provide key-point-based answers."},
                {"role": "user", "content": user_question}
            ]
        }

        response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload)

        if response.status_code != 200:
            return jsonify({"error": "Failed to get AI response"}), 500

        response_data = response.json()
        raw_answer = response_data["choices"][0]["message"]["content"]

        # Convert AI response to a bullet-point format
        answer_list = raw_answer.split("\n")
        formatted_answer = "<ul>" + "".join(f"<li>{point.strip()}</li>" for point in answer_list if point.strip()) + "</ul>"

        return jsonify({"answer": formatted_answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500





# ✅ Handle Image-Based Queries (PlantNet API)
@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        url = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"
        print(f"Sending request to: {url}")  # Debugging URL issue

        with open(file_path, "rb") as image_file:
            files = {"images": image_file}
            data = {"organs": "leaf"}  # Corrected format
            response = requests.post(url, files=files, data=data)

        if response.status_code != 200:
            return jsonify({"error": "Failed to process image", "details": response.text}), response.status_code

        result = response.json()
        if "results" not in result or not result["results"]:
            return jsonify({"error": "No plant identification found"}), 404

        top_result = result["results"][0]
        species_name = top_result["species"]["scientificNameWithoutAuthor"]
        confidence = round(top_result["score"] * 100, 2)

        return jsonify({
              "scientific_name": species_name,
              "common_name": top_result["species"].get("commonNames", ["Not available"])[0],
              "family_name": top_result["species"].get("family", {}).get("scientificNameWithoutAuthor", "Not available"),
              "confidence": f"{confidence}%"
             })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Update the news fetching function to include pagination (limit and offset)
def get_agriculture_news(offset=0, limit=5):           
    url = f"https://gnews.io/api/v4/search?q=agriculture&lang=en&token=9e7c99dc55b051ea8777dad9ff221f0f&start={offset}"
    response = requests.get(url)
    news_data = response.json()
    articles = news_data['articles']# No selection was made, so there's no code to modify.
    
    # Select the news articles
    top_news = []
    for article in articles[:limit]:
        top_news.append({
            'title': article['title'],
            'description': article['description'],
            'url': article['url'],
            'image': article['image']
        })
    return top_news

# Endpoint to fetch agriculture news with pagination
@app.route('/get_agriculture_news', methods=['GET'])
def agriculture_news():
    offset = int(request.args.get('offset', 0))  # Get offset value from query params
    limit = int(request.args.get('limit', 5))  # Limit value for pagination
    news = get_agriculture_news(offset, limit)
    return jsonify(news)




def scrape_prices(commodity, date):
    state = "himachal-pradesh"
    commodity_slug = commodity.replace(" ", "-").lower()
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d-%b-%Y").lower()
    except ValueError:
        return [], "Invalid date format. Please use YYYY-MM-DD."

    url = f"https://www.napanta.com/agri-commodity-prices/{state}/{commodity_slug}/{formatted_date}"
    response = requests.get(url)
    if response.status_code != 200:
        return [], f"Failed to retrieve data from {url}. Status code: {response.status_code}"

    soup = BeautifulSoup(response.content, 'html.parser')
    prices = []
    rows = soup.select("table tbody tr")

    for row in rows:
        columns = row.find_all("td")
        if len(columns) >= 7:
            prices.append({
                "district": columns[0].get_text(strip=True),
                "market": columns[1].get_text(strip=True),
                "commodity": columns[2].get_text(strip=True),
                "variety": columns[3].get_text(strip=True),
                "max_price": columns[4].get_text(strip=True),
                "avg_price": columns[5].get_text(strip=True),
                "min_price": columns[6].get_text(strip=True),
                "updated_on": formatted_date,
            })

    if not prices:
        return [], f"No data found for {commodity} on {formatted_date} in Himachal Pradesh."

    return prices, ""





URL = 'https://sarkariyojana.com/himachal-pradesh/'

def scrape_data():
    response = requests.get(URL)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('article')

    schemes = []
    for article in articles:
        title_tag = article.find('h2', class_='entry-title')
        title = title_tag.text.strip() if title_tag else 'No Title'
        link = title_tag.find('a')['href'] if title_tag and title_tag.find('a') else '#'

        img_tag = article.find('img')
        img_src = img_tag['src'] if img_tag else ''

        # Skip fetching descriptions to speed up
        schemes.append({
            'title': title,
            'link': link,
            'img_src': img_src,
            'desc': "Click to read more on the official site"  
        })

    return schemes


def fetch_description(link):
    try:
        response = requests.get(link)
        if response.status_code != 200:
            return 'No description available'

        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='entry-content')
        if not content_div:
            return 'No description available'

        # Extract the first paragraph as the description
        first_paragraph = content_div.find('p')
        if first_paragraph:
            return first_paragraph.text.strip()
        else:
            return 'No description available'
    except Exception as e:
        return 'No description available'









@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", state="Himachal Pradesh")

# Route to fetch crop prices
@app.route("/get_prices", methods=["POST"])
def get_prices():
    commodity = request.form.get("commodity")
    date = request.form.get("date")

    prices, message = scrape_prices(commodity, date)

    if not prices:
        return jsonify({"message": message})

    return jsonify({"prices": prices})

# Route to fetch government schemes
@app.route("/get_schemes", methods=["GET"])
def get_schemes():
    schemes = scrape_data()
    return jsonify(schemes)















if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    print(app.url_map)  # 🔥 Now this will print the correct routes!
    app.run(host="0.0.0.0", port=5000, debug=True)

