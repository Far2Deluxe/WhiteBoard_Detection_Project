# 🖼️📚 Whiteboards Detection Project

A smart tool that **scans your Pictures/Gallery folder** and detects **photos containing whiteboards**, helping students easily separate **school/college-related images** from personal photos.  

🚀 Built with a **YOLOv8-trained custom model** for whiteboard detection and a **QT-based GUI** for a smooth user experience.  

----------------------------------------------------------------------------------------------------------------------------------------------

## ✨ Features  
- 🤖 **YOLOv8-powered detection** – trained locally on custom datasets.  
- 🖼️ **Smart photo scanning** – automatically finds whiteboards in pictures.  
- 📂 **Auto-organization** – moves detected whiteboard images into a dedicated `Whiteboards/` folder.  
- 💻 **User-friendly GUI** – designed with QT for simplicity and accessibility.  
- 🎓 **Student-focused** – keeps study photos separate from personal memories.  
- 🔍 **Batch Processing** - Scan entire photo libraries efficiently

----------------------------------------------------------------------------------------------------------------------------------------------

## 🏗️ Project Structure  
```bash
├── src/                # Main source code
│   ├── data/           # Contains Yolo Training Codes
│   ├── gui/            # Modren QT GUI
│   ├── detection/      # Has detection functions 
│   ├── models/         # Contains trained models
│   └── utils/          # Helper scripts
├── data/               # Conatins Data Images and Labels
├── doc/                # Contains Documention Files
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Has project dependencies and requirements
├── UV.lock             # Auto Generated to lock dependencies to a certain version
└── README.md           # Project documentation
```
----------------------------------------------------------------------------------------------------------------------------------------------

## 🛠️ Installation & Setup

### 📋 Prerequisites
- Python 3.13.5 or higher
- UV package manager

## 👣 Steps

# 1. Clone the repository:

    git clone https://github.com/Far2Deluxe/WhiteBoard_Detection_Project
    cd WhiteBoard_Detection_Project


# 2. Install Dependencies:
You can auto download all requirements by using command:

      uv sync
      
- or use offline installation by placing wheels folder inside the project directory and running "Libs Installer.py" script
  which will create the environment and installs all dependencies offline using UV. (wheels folder will be provided via USB due to large size)

# 3. Open the cloned folder in VScode/Cursor:
- Then use the .vevn enviroment created in project folder so that the depenecies are recognized.
- if the environment is not recognized by vscode/cursor, run .venv/scripts/activate.bat and then from vscode/cursor add interprter by path .venv/scripts/python.exe
- open main.py and run it, it should show the GUI.


### 📚 Training codes and Utilite codes are mentioned in notebooks/notebook.ipynb


----------------------------------------------------------------------------------------------------------------------------------------------

## 🧠 How It Works
- Image Loading: Reads images from specified directory.
- Object Detection: Uses YOLOv8 to identify whiteboards.
- Classification: Separates images with/without whiteboards.
- Organization: Moves files to appropriate folders.
- Reporting: Provides summary of processing results.


----------------------------------------------------------------------------------------------------------------------------------------------

## ❓ How to Use it ?
When First running the GUI you would be faced with the following features:
- Button to explore folder and select your photos folder you want to filter out whiteboard images from. You would then be shown the images inside that folder.
- Button to start the detection process. Images that got detected would be displayed on the GUI
- Two Extra buttons would appear, one to exclude selected photos from the detection in case of miss-detection by the model, the other button is to proceed the process of moving all detected photos away into a newly created Folder "Whiteboards" in the root of your photos folder.
- There is a Confidence Threshold slider which will change the threshold point at which the model detects a photo to be a whiteboard.
- A drop down menu allowing User to select from available models in project folders or select a custom model via explorer.

----------------------------------------------------------------------------------------------------------------------------------------------

## 👥 Team Members  

| AC.NO | Name            | Role           | Contributions                        |
|-------|-----------------|----------------|--------------------------------------|
| 202270029     | Fares Haider    | Lead Developer | Data preprocessing, model development, model optimiztion |
| 202270096     | Hayel Ehab        |   Interface Designer  | Graphical User Interface GUI, datasets integration |
| 202270398     | Luay Zayed        | Model Developer | Model training, data labeling, model testing       |
| 202270132     | Osama Al-Qubati  | Data Analyst  | Data collection , data labeling, model deployment |


----------------------------------------------------------------------------------------------------------------------------------------------

## ⚒️✨ Models Changelogs :

### Whiteboard Model4
- Yolo Model: Yolov8s.pt
- Epochs: 70 (best.pt at 35 epoch due to patience parameter)
- Used "YoloV8TrainerCUDA_V2.py" in src/data to train
- Detailed training results are in src/models/Whiteboard Model4/
- From Personal Test, out of 800 images falsely detected 16 images.

----------------------------------------------------------------------------------------------------------------------------------------------

