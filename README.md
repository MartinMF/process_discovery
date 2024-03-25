# Process Discovery: Inductive Miner Lifecycle Extension

This project involves the development of a web application aimed at stream-based process discovery. The application connects to a running instance of CPEE (Cloud Process Execution Engine) executing one of four predefined models: TUM-Pra-WS-23-Discovery1, TUM-Benzin-Pra-WS-23-2, TUM-Benzin-Pra-WS-23-3, and Coopis 2010. It continuously records the event stream and uses the Inductive Miner Lifecycle Extension process discovery technique to construct a Petri net representing the current behavior.

## Functionality

- Connects to a CPEE instance and records the event stream
- Discovers Petri Net based on the Inductive Miner Lifecycle Extension process discovery technique
- Allows configuration of stream-based process discovery technique:
  - Choice of CPEE model in execution: TUM-Pra-WS-23-Discovery1, TUM-Benzin-Pra-WS-23-2, TUM-Benzin-Pra-WS-23-3, and Coopis 2010
  - Update frequency options: time step-based, event-based, or batch event-based
- Visualizes discovered Petri Net using GraphViz
- Provides interactive analysis features:
  - Zoom in/out
  - Select and focus specific elements
  - Reverse selection
  - Save/download current visualization
- Enriches model elements with metrics describing their currency based on event timestamps
- Constraint: Python backend

---

## Setup

Clone this repository and install the requirements.

```bash
git clone https://github.com/MartinMF/process_discovery.git
cd process_discovery
pip install -r requirements.txt
```

---

## Usage

### Starting the Server

Running the `run.py` script will start the server on localhost:8000.

```bash
python run.py
```

### Operating the Web Application

Once the server is running, visit localhost:8000 for the web interface.

1. Select one of the predefined CPEE models:
    - TUM-Pra-WS-23-Discovery1
    - TUM-Benzin-Pra-WS-23-2
    - TUM-Benzin-Pra-WS-23-3
    - Coopis 2010.

    ![image](https://i.postimg.cc/QdcJLkJ5/process-selection.png)

2. Select how many instances of the selected model should be executed.

    ![image](https://i.postimg.cc/kX0vhhKq/instance-amount.png)

3. Choose an update mode:
    - Time interval: The model will pull updates every X milliseconds.
    
        ![image](https://i.postimg.cc/jjMGYbRG/update-mode.png)

    - Event-based: The server will push an update every X events from the instances.
    
        ![image](https://i.postimg.cc/0ysgpntH/update-mode-event.png)
   
4. Input the interval in ms or the batch-size for the event-based updating.

     ![image](https://i.postimg.cc/Wpxc4T0V/interval.png)

     ![image](https://i.postimg.cc/t4tKD6wR/batch-size.png)
   
5. Click the "Run" button to start the execution of the instances and updates the displayed Petri net and corresponding model information based on the selected update mode.
6. Click the "Stop" button to halt the model updating. Note: The instances will continue to run in the background.
7. Click the "Clear logs" button to delete all collected event-information from the log.

Hold right click to move the Petri Net around, click an element to see relevant information and scroll to zoom in/out 

### Instance colors:

    - Green: Process instance finished
    - Yellow: Process instance stopped and was restarted
    - Red: Process instance stopped and was not restarted (restarted too often)
    - Blue: Process instance is still running

---

## Technologies Used

- Python for backend development ([Flask](https://github.com/pallets/flask))
- HTML/CSS/JS for web interface development
- [GraphViz](https://graphviz.org/) library for Petri net representation
- Integration with [CPEE](https://cpee.org/) for event stream retrieval
