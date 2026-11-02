# What I Learned from This Project

While working on the Smart Box Selection System, I learned how to build a small web application using Django and Django REST Framework.

I learned how to:
- Create Django models for products, boxes, orders, and order items.
- Use a database to store product and box details.
- Write logic to recommend a suitable box based on product dimensions, weight, and cost.
- Create API endpoints to view products and boxes and submit orders.
- Connect a webpage form to the backend using JavaScript and fetch requests.
- Use Django templates, static files, and CSRF tokens.
- Write and run test cases to check the box recommendation logic.
- Use Git and GitHub to save and share my project.

I also learned that debugging is an important part of development. I faced issues with URL routing, loading products in the webpage, and submitting orders. By checking the errors and testing the changes, I learned how to find and fix problems.

One limitation of my current project is that it checks whether each product fits individually in a box. It does not yet calculate whether all products can fit together in the same box. I would like to improve this in the future by adding a proper 3D packing algorithm.