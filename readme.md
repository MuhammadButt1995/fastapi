# Talos FastAPI Backend

## Description

This project serves as the backend for the Talos application.  
The frontend is located here (provide link)  
The main.py file servers as the main entry of this backend.

## Requirements

Make sure you have Python 3.8 or later installed.

## Setting Up

### For Windows Users

1. **Create a virtual environment**

   Open your command prompt and navigate to the project directory, then run:

   ```
   python -m venv venv
   ```

2. **Activate the virtual environment**

   ```
   .\venv\Scripts\activate
   ```

3. **Install the required packages**

   ```
   pip install -r requirements.txt
   ```

### For Mac Users

1. **Create a virtual environment**

   Open your terminal and navigate to the project directory, then run:

   ```
   python3 -m venv venv
   ```

2. **Activate the virtual environment**

   ```
   source venv/bin/activate
   ```

3. **Install the required packages**

   ```
   pip3 install -r requirements.txt
   ```

## Running the App

Once you have your environment setup and activated, you can run the FastAPI app using Uvicorn. Here is the command to do that:

```
uvicorn main:app --reload
```

This command refers to:

- `main`: the file `main.py` (the Python "module").
- `app`: the object created inside `main.py` with the line `app = FastAPI()`.
- `--reload`: make the server restart after code changes. Only do this for development.

Visit http://localhost:8000/tools in your browser to see the list of available tools sent to the frontend  
To execute a tool, visit http://localhost:8000/tools/{tool-id} where {tool-id} is the name of the tool you want to execute
