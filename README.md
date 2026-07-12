# 💧 Smart Water Management System

A data science project for monitoring and managing household water usage. This system generates and analyzes water consumption data, exposes it through a backend API, and visualizes it on an interactive dashboard to help households track usage, spot anomalies, and promote conservation.

## 📌 Overview

Household water consumption is often invisible until the bill arrives. This project aims to close that gap by:

- Generating/collecting sample water usage data
- Serving that data through a backend API
- Displaying usage trends and insights on a web-based dashboard
- Documenting the methodology and findings in a formal report and presentation

## ✨ Features

- 📊 **Interactive Dashboard** — Visualize household water usage trends in real time (`Smart_Water_Dashboard.html`)
- 🔌 **Backend API** — Serves water usage data to the dashboard (`backend_api.py`)
- 🧪 **Sample Dataset Generator** — Script to create synthetic/sample water usage data (`generate_dataset.py`)
- 📁 **Sample Dataset** — Ready-to-use dataset for testing and demos (`Water_Usage_Sample_Dataset.xlsx`)
- 📄 **Project Report** — Detailed write-up of approach, methodology, and results (`Smart_Water_Monitoring_Report.docx`)
- 🖥️ **Presentation** — Summary slides for project walkthroughs (`Smart_Water_Monitoring_Presentation.pptx`)

## 🗂️ Project Structure

```
smart-water-management-system/
├── backend_api.py                          # Backend API serving usage data
├── generate_dataset.py                     # Script to generate sample dataset
├── Water_Usage_Sample_Dataset.xlsx          # Sample water usage dataset
├── Smart_Water_Dashboard.html               # Frontend dashboard
├── Smart_Water_Monitoring_Report.docx       # Project report
├── Smart_Water_Monitoring_Presentation.pptx # Project presentation
├── LICENSE                                  # MIT License
└── README.md                                # Project documentation
```

## 🛠️ Tech Stack

- **Backend:** Python
- **Frontend:** HTML, CSS, JavaScript
- **Data:** Excel (.xlsx)
- **Documentation:** Word, PowerPoint

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/chaitanyanalabolu/smart-water-management-system.git
   cd smart-water-management-system
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Generate the sample dataset (optional — a sample is already included)
   ```bash
   python generate_dataset.py
   ```

4. Run the backend API
   ```bash
   python backend_api.py
   ```

5. Open the dashboard
   Open `Smart_Water_Dashboard.html` in your browser to view the visualizations.

## 📊 Dataset

`Water_Usage_Sample_Dataset.xlsx` contains sample household water usage records used to power the dashboard and demonstrate the system's analysis capabilities.

## 📄 Documentation

- **Report:** See `Smart_Water_Monitoring_Report.docx` for the full methodology, analysis, and conclusions.
- **Presentation:** See `Smart_Water_Monitoring_Presentation.pptx` for a slide-based summary of the project.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to open an issue or submit a pull request.

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Chaitanya Nalabolu**
GitHub: [@chaitanyanalabolu](https://github.com/chaitanyanalabolu)
