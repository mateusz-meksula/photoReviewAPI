# <img src="./photoreviewapi_header.jpg">

## About the Project

Photo Review API is a web API that allows users to upload and rate images.  
The API has the following functionalities:
<ul>
    <li>user registration along with password reset functionality</li>
    <li>JWT authentication</li>
    <li>image upload</li>
    <li>tags system for images</li>
    <li>rating system for images</li>
</ul>

Account management for the API is provided by [flash-accounts](https://github.com/mateusz-meksula/flash-accounts) package, and JWT authentication is provided by [djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt) plugin.

Photo Review API was built with Django and Django REST Framework, with data managed by a PostgreSQL database.

## Overview

Photo Review API has the following endpoints:

```python
- /api/auth/sign-up/
- /api/auth/password-reset/
- /api/auth/password-reset/confirm/<str:token>/
- /api/auth/token/
- /api/auth/token/refresh/

- /api/photos/
- /api/photos/<int:photo_id>/
- /api/photos/<int:photo_id>/reviews/
- /api/photos/<int:photo_id>/reviews/<int:review_id>/

- /api/tags/
- /api/tags/<str:tag_name>/
```

## Challenges & Solutions

### Image files handling

### Tag system

### Review system

### Nested urls for reviews

## Frontend JavaScript client

## Running project locally