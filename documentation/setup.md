# Project Setup Guide

## 🔧 Installation

### 1. Environment Setup

```bash
# Navigate to project directory
cd PySportXSkillCornerChallengeAnalytics

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Jupyter (Optional)

```bash
# Add virtual environment to Jupyter
python -m ipykernel install --user --name=pysport_analytics --display-name="PySport Analytics"
```

## 📁 Directory Structure

```
PySportXSkillCornerChallengeAnalytics/
├── README.md                          # Entry point
├── app.py                             # Main Streamlit Application
├── requirements.txt                   # Dependencies
├── src/                               # Source code
│   ├── data_loader.py                 # Data utilities
│   ├── metrics.py                     # xG models and metrics
│   ├── visualizations.py              # Plotting logic
│   └── utils.py                       # Helper functions
├── pages/                             # Streamlit Pages
│   ├── 1_Match_Overview.py
│   ├── 2_Player_Analysis.py
│   └── ...
└── documentation/                     # Project Documentation
    ├── setup.md
    └── ...
```

## 🏃 Running the Application

There are two primary ways to run the application:

### Option 1: Via Shell Script (Recommended)
This script automatically activates the environment and runs the app.

**Windows:**
```cmd
run_app.bat
```

**Linux/Mac:**
```bash
./run_app.sh
```

### Option 2: Manual Start
```bash
streamlit run Home.py
```
