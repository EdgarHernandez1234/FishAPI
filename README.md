# FishScore

FishScore is a full-stack web application that evaluates fishing conditions and gives each day a score from 1 to 10. The application retrieves weather data from the National Weather Service API, processes it through fishing-condition scoring logic, and presents the results through a JavaScript and HTML frontend.

Users can also participate in a discussion board by creating and viewing posts stored in a MongoDB database.

## Live Application

- Frontend: https://fishscorer.onrender.com
- Backend API: https://fishscore.onrender.com

## Features

- Fishing-condition scores from 1 to 10
- Weather data from the National Weather Service API
- Custom scoring calculations based on forecast conditions
- Interactive frontend for viewing fishing recommendations
- Discussion board for creating and viewing posts
- MongoDB persistence for user-generated posts
- REST API built with FastAPI
- Deployed frontend and backend services

## Technology Stack

### Backend

- Python
- FastAPI
- REST APIs
- National Weather Service API
- MongoDB
- MongoDB Atlas

### Frontend

- HTML
- JavaScript
- CSS

### Deployment and Collaboration

- GitHub
- Render
- Git

## Application Architecture

```text
National Weather Service API
              |
              v
     FastAPI Backend
              |
     -------------------
     |                 |
     v                 v
Scoring Logic       MongoDB
     |                 |
     v                 v
JavaScript/HTML Frontend
```

The backend retrieves weather information from the National Weather Service API and processes the data through custom scoring logic. The resulting fishing score is returned to the frontend through API endpoints.

MongoDB is used to store discussion-board posts so users can create and retrieve shared content.

## API Endpoints

Some of the primary backend routes include:

- `GET /api/spots` - Retrieves available fishing locations
- `GET /api/spots/{spot}/score` - Calculates a fishing score for a selected location
- `GET /api/posts` - Retrieves discussion-board posts
- `POST /api/posts` - Creates a new discussion-board post

## Local Setup

### Clone the repository

```bash
git clone [YOUR_GITHUB_REPOSITORY_URL]
cd [YOUR_PROJECT_DIRECTORY]
```

### Backend setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file and add the required MongoDB connection settings:

```env
MONGODB_URI=your_mongodb_connection_string
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

### Frontend setup

Open the frontend files in a local development server, such as the VS Code Live Server extension, and make sure the frontend is configured to send requests to the local FastAPI backend.

## Example Use Case

A user selects a fishing location. FishScore retrieves the relevant weather forecast, evaluates conditions such as temperature, wind, and other weather factors, and returns a score from 1 to 10. The user can then decide whether the forecasted conditions are favorable for fishing.

Users can also create posts to discuss locations, conditions, and fishing experiences with other users.

## Future Improvements

- User authentication and accounts
- Additional fishing locations
- More detailed scoring explanations
- Improved mobile responsiveness
- User profiles and post editing
- Search and filtering for discussion posts
- Automated testing for scoring calculations and API routes
- More detailed weather visualizations

## Contributors

This project was created collaboratively as part of a hackathon.

## Demo Video

https://youtu.be/bOBCmlpe0yk
