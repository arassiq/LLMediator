# LLMediator

**LLMediator** is a real-time AI-powered mediation platform that helps resolve disputes between two parties (plaintiff and defendant). Built using Flask, Flask-SocketIO, and OpenAI's GPT-4, it facilitates turn-based conversations and helps parties negotiate settlements with automated assistance.

## Features

- **Real-time Chat**: Facilitates live, turn-based mediation sessions between a plaintiff and a defendant.
- **AI Mediation**: Utilizes OpenAI's GPT-4 model to assist in mediation, offering suggestions and evaluating the positions of both parties.
- **Dynamic Role Management**: Manages separate communication channels for plaintiff and defendant.
- **Cross-Platform Support**: Frontend built with HTML, CSS, and JavaScript; Backend built using Flask and Flask-SocketIO for WebSocket support.

## Prerequisites

Make sure you have the following installed on your machine:

- [Python 3.x](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [Node.js](https://nodejs.org/) (for frontend, if needed for dependencies)

## Getting Started

### Step 1: Clone the Repository

1. Open a terminal and run the following command to clone the repository:

   ```bash
   git clone https://github.com/your-username/LLMediator.git
   ```
   
2.	Navigate into the project directory:
       
    ```bash
    cd LLMediator
    ```
### Step 2: Set Up the Backend

1. Navigate to the backend directory:
 
    ```bash
    cd backend
    ```

2. Create a virtual environment (optional but recommended):
On macOS/Linux:
   
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

    On Windows:

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

4.	Install dependencies:
Run the following command to install all Python packages from the requirements.txt file:
    ```bash
    pip install -r requirements.txt
    ```
5.	Set up the OpenAI API key:
You’ll need an OpenAI API key to use GPT-4. You can set it up using environment variables or a .env file.
- First, create a .env file in the backend directory:
    ```bash
    touch .env
    ```
- Open the .env file in a text editor and add your OpenAI API key:
    ```bash
    OPENAI_API_KEY=your_openai_api_key_here
    ```
- Replace your_openai_api_key_here with your actual OpenAI API key.

- Alternatively, you can export the key in your terminal session (if you’re not using a .env file):
  On macOS/Linux:
    ```bash
    export OPENAI_API_KEY=your_openai_api_key_here
    ```
    On Windows (Command Prompt):
    ```bash
    set OPENAI_API_KEY=your_openai_api_key_here
    ```
5.	Run the Backend Server:
After setting up the API key, start the backend server with:
    ```bash
    python core.py
    ```
The server will now be available at http://localhost:5002.

Step 3: Set Up the Frontend

1.	Navigate to the frontend directory:
    ```bash
    cd ../frontend
    ```
2.	Serve the frontend:
You can serve the frontend files using any static file server. Here are two examples:
- Using Python:
    ```bash
    python -m http.server 8000
    ```
The frontend will be available at http://localhost:8000.

•	Using Node.js (if you have it installed):
First, install http-server globally (if you don’t have it):
    ```bash
    npm install -g http-server
    ```
Then, serve the frontend:
    ```bash
    http-server -p 8000
    ```

The frontend will now be accessible at http://localhost:8000.
    
### Step 4: Testing the Application

	1.	Open two browser windows (or tabs) and navigate to http://localhost:8000.
	2.	In one window, register as the plaintiff, and in the other window, register as the defendant.
	3.	Follow the prompts, and the AI mediator will assist both parties in resolving the dispute.

## Project Structure
```bash
LLMediator/
├── backend/
│   ├── core.py             # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── .env                # Environment file for API keys
│   └── .gitignore          # only track necessary files
├── frontend/
│   ├── frontend.html       # Main frontend HTML file
│   └── ...                 # Other frontend files
└── README.md               # Project documentation
```

## Dependencies

### Backend (Python):

- Flask: A micro web framework.
- Flask-SocketIO: Real-time communication support for Flask.
- OpenAI: Interacts with OpenAI’s GPT-4 model.
- eventlet/gevent: For asynchronous handling in Flask-SocketIO.
- python-dotenv: For loading environment variables from a .env file.

### Frontend:

•	HTML/CSS/JavaScript: No external libraries, but you can use npm or other package managers if needed.

License

This project is licensed under the MIT License - see the LICENSE file for details.
