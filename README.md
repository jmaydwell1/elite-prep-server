# ElitePrep Mobile Server

Backend server for the ElitePrep mobile application.

## Setup

1. Create a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your environment variables:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the server:
```bash
uvicorn main:app --reload
```

## API Endpoints

- `POST /register` - Register a new user
- `POST /login` - Login a user
- `POST /onboarding` - Update user onboarding data
- `POST /performance-trends` - Add performance trends
- `GET /performance-averages/{email}` - Get performance averages
- `POST /generate` - Generate content using OpenAI

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key
