import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
from urllib.parse import quote
import logging as lg
from flask import Flask, render_template, request, redirect, send_file
import pymongo
from dotenv import load_dotenv
from decouple import config
import csv

# Load environment variables from the .env file
load_dotenv()

# mongo Config


# Config Log
log_format = '%(asctime)s - %(levelname)s - %(message)s'
log_file = 'web_scrapping_log.log'
lg.basicConfig(filename=log_file, level=lg.INFO, format=log_format)

# Flask
app = Flask(__name__)

# Get MongoDB connection string from environment variables
mongo_db_connection = config('MONGO_DB_CONNECTION')


@app.route('/download_csv', methods=['GET'])
def download_csv():
    try:
        # Create a connection to MongoDB
        client = pymongo.MongoClient(mongo_db_connection)
        db = client['Web_Scrap']
        web_Coll = db['FlipKart_Reviews']

        data = list(web_Coll.find())

        # Close the MongoDB connection
        client.close()

        # Prepare data for CSV
        csv_data = [['Name', 'Rating', 'Comment Header', 'Comment']]
        for item in data:
            csv_data.append([item.get('name'), item.get('rating'), item.get('comment_header'), item.get('comment')])

        # Create a temporary CSV file
        with open('scraped_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(csv_data)

        # Return the CSV file as a downloadable attachment
        return send_file('scraped_data.csv', as_attachment=True, download_name='scraped_data.csv')
    except Exception as e:
        # Log the exception to both the file and MongoDB
        lg.error("Exception Occurred: %s", str(e))
        log_to_mongodb('ERROR', 'Exception occurred while downloading CSV: ' + str(e))
        # Return an error message to the user
        return 'Something Went Wrong'


def log_to_mongodb(level, message):
    try:
        # Create a connection to MongoDB
        client = pymongo.MongoClient(mongo_db_connection)
        db = client['Web_Scrap']
        log_Coll = db['Logs']  # Create a collection for logs

        # Insert log data into MongoDB
        log_Coll.insert_one({'level': level, 'message': message})

        # Close the MongoDB connection
        client.close()
    except Exception as e:
        # If an error occurs while logging to MongoDB, log it to the file
        lg.error("Error logging to MongoDB: %s", str(e))


@app.route('/', methods=['GET'])
def homepage():
    return render_template('index.html')


@app.route('/delete', methods=['POST'])
def delete_data():
    try:
        # Create a connection to MongoDB
        client = pymongo.MongoClient(mongo_db_connection)
        db = client['Web_Scrap']
        web_Coll = db['FlipKart_Reviews']
        log_Coll = db['Logs']

        # Delete all data from the collection
        web_Coll.delete_many({})
        log_Coll.delete_many({})

        # Close the MongoDB connection
        client.close()

        # Redirect to the homepage after deletion
        return redirect('/')
    except Exception as e:
        # Log the exception to both the file and MongoDB
        lg.error("Exception Occurred: %s", str(e))
        log_to_mongodb('ERROR', 'Exception occurred while deleting data: ' + str(e))

        # Return an error message to the user
        return 'Something Went Wrong'


@app.route('/scrapp', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':

        try:
            query = quote(request.form['content'])
            num_review = int(request.form['num_review'])

            momgo = []
            flipkart_url = "https://www.flipkart.com/search?q=" + query
            urlClient = uReq(flipkart_url)
            flipkart_page = urlClient.read()
            flipkart_html = bs(flipkart_page, 'html.parser')
            products = flipkart_html.findAll('div', {'class': '_1AtVbE col-12-12'})
            del products[0:3]
            product_link = []
            for product in products:
                product_anchor = product.find('a')  # Find the 'a' tag within the product div
                if product_anchor:
                    href = product_anchor.get('href')  # Get the 'href' attribute
                    if href:
                        product_link.append('https://www.flipkart.com' + href)
            for index, i in enumerate(product_link):
                if index >= num_review:
                    break
                product_req = requests.get(i)
                product_html = bs(product_req.text, 'html.parser')
                product_com = product_html.findAll('div', {'class': "_16PBlm"})
                for product_coms in product_com:
                    name_elem = product_coms.find('p', {'class': "_2sc7ZR _2V5EHH"})
                    rating_elem = product_coms.find('div', {'class': "_3LWZlK _1BLPMq"})
                    header_elem = product_coms.find('p', {'class': "_2-N8zT"})
                    comment_elem = product_coms.find('div', {'class': ''})
                    if name_elem and rating_elem and header_elem and comment_elem:
                        name = name_elem.text
                        rating = rating_elem.text
                        comment_header = header_elem.text
                        comment = comment_elem.text
                        comment = comment.split("READ MORE")[0].strip()

                        mydict = {

                            'name': name,
                            'rating': rating,
                            'comment_header': comment_header,
                            'comment': comment
                        }

                        momgo.append(mydict)
                        client = pymongo.MongoClient(mongo_db_connection)
                        db = client['Web_Scrap']
                        web_Coll = db['FlipKart_Reviews']
                        for item in momgo:
                            if isinstance(item, dict):
                                # Use the 'name' field as the _id
                                name = item.get('name')

                                if name:
                                    # Check if a document with the same 'name' already exists
                                    existing_doc = web_Coll.find_one({'name': name})

                                    if existing_doc:
                                        # Document with the same 'name' already exists, you can skip it
                                        lg.warning("Duplicate document found for 'name': %s", name)
                                    else:
                                        # Insert the document with the 'name' as _id
                                        item['_id'] = name
                                        web_Coll.insert_one(item)
                                else:
                                    lg.warning("Document missing 'name' field: %s", str(item))
                            else:
                                lg.warning("Invalid data format: %s", str(item))
            lg.info("DATA ADDED SUCCESSFUL")
            log_to_mongodb('INFO', 'Scraping completed successfully.')

            data = list(web_Coll.find())

            # Close the MongoDB connection
            client.close()

            return render_template('return.html', data=data, query=query)


        except Exception as e:

            # Log the exception to both the file and MongoDB

            lg.error("Exception Occurred: %s", str(e))

            log_to_mongodb('ERROR', 'Exception occurred during scraping: ' + str(e))

            # Return an error message to the user

            return 'Something Went Wrong'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
