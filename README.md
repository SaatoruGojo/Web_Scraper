# Flipkart Review Scraper

This Python application scrapes product reviews from Flipkart and provides the user with the ability to view the reviews
in a tabular format and download them as a CSV file.

## Features

- Scrapes product reviews from Flipkart based on user input.
- Displays review data in a tabular format.
- Allows users to download the review data in a CSV file.
- Logs errors and activity to both a file and a MongoDB database.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.6 or higher installed.
- Required Python packages listed in `requirements.txt`. You can install them using `pip install -r requirements.txt`.
- MongoDB set up with the appropriate connection string in your environment variables.
- Create a `.env` file with your MongoDB connection string:
