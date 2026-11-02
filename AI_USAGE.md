# AI Usage

## 1. AI Tool Used
I used Antigravity, an AI coding assistant, to understand the assignment, get help with Django code, and fix errors during development.

## 2. Prompts I Gave
Some of the prompts I used were:
- “Help me create a Django project for an AI-assisted box selection system.”
- “Give me the models for products, boxes, orders, and order items.”
- “Help me write the logic to recommend a suitable box based on product dimensions, weight, and cost.”
- “Help me create API endpoints for products, boxes, and orders.”
- “Help me create a simple webpage to submit an order and display the recommended box.”
- “Help me fix the errors I got while running the project and tests.”

## 3. Output I Accepted
I used suggestions for the Django models, API structure, box recommendation logic, webpage form, and test cases. I reviewed the code and adjusted it to fit my project.

## 4. Output I Rejected or Modified
I changed some suggested code when it did not match my project structure or caused errors. I also updated the weight-capacity test after checking the box limits in my test data.

## 5. Mistakes Made by AI
Some suggestions did not work correctly with my project at first. I had issues with the webpage route, product dropdown, and CSRF token. I tested the suggestions and made changes to fix these issues.

## 6. How I Verified the Final Code
I ran the Django development server and checked the webpage in the browser. I tested the product and box API endpoints, submitted an order through the webpage, and ran the Django tests using:

`python manage.py test boxes`

I checked the test output to confirm the tests passed.