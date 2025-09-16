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

🛠️ Installation Steps

1. Clone the repository:

    git clone https://github.com/Far2Deluxe/WhiteBoard_Detection_Project
    cd WhiteBoard_Detection_Project


2. Install Dependencies:
You can auto download all requirements by using command:

        uv sync
        or use offline installtion by placing wheels folder inside the project directory and running "Libs Installer.py" script
        which will create the environment and installs all dependencies offline using UV. (wheels folder will be provided via USB due to large size)

----------------------------------------------------------------------------------------------------------------------------------------------

🧠 How It Works
    1.Image Loading: Reads images from specified directory.
    2.Object Detection: Uses YOLOv8 to identify whiteboards.
    3.Classification: Separates images with/without whiteboards.
    4.Organization: Moves files to appropriate folders.
    5.Reporting: Provides summary of processing results.


----------------------------------------------------------------------------------------------------------------------------------------------
