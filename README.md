# Dukadawa-OCR

## Using the API

The server is running and accessible at `http://127.0.0.1:8000`.

### API Documentation

You can access the API documentation to explore the endpoints and schemas:

* **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### API Usage

To use the API endpoints, follow these steps:

1. **Register a user**: Use the `/register` endpoint to create a new user account.
2. **Get an access token**: Use the `/token` endpoint with your username and password to obtain an access token.
3. **Authorize in Swagger UI (Optional)**: If using Swagger UI, click the "Authorize" button and enter your access token to authenticate your requests.
4. **Process images**: You can now use the image processing endpoints:
    * `/api/v1/process-image/`: For processing single images.
    * `/api/v1/process-bulk/`: For processing multiple images.

**Key features:**

* **Authentication**: User authentication is enabled and working.
* **Database**: Processed data is stored in an SQLite database.
* **Optional Redis**: The API functions correctly even without Redis (caching and rate limiting will be disabled).
* **Documentation**: API documentation is available through Swagger UI and ReDoc.
