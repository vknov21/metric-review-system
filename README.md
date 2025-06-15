# 📊 Metric Review System

**Metric Review System** is a lightweight, extensible web application for conducting peer reviews based on customizable performance metrics. Built with [Streamlit](https://streamlit.io/), it enables teams to collect, manage, and analyze feedback efficiently through a simple browser-based interface.

---

## 🚀 Getting Started

### 📦 Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/vknov21/metric-review-system
   cd metric-review-system
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Customize the Config to add the peers to review**
   Go to the config.py file, and modify the necessary entries.

### ▶️ Running the App

Start the application using Streamlit:
```bash
streamlit run metric_review.py
```

- The app opens in your default browser.
- Select your reviewer name from the dropdown to begin a session.
- Fill in ratings for each teammate based on the defined metrics.
- Confirm and submit your reviews.

---

## ✨ Features

### 🖥️ User Interface

- **Browser-based experience** – no installation required for end users.
- **Session Management:** Each reviewer logs in with a unique identity and can review each other or assigned users.
- **Live Validation:** All inputs are validated for proper range and type before submission.
- **Progress Tracking:** Once a review is finalized, it is locked to prevent duplicate submissions.
- **Confirmation Dialogs:** Confirms before final submission for each review.

### 📊 Metrics & Customization

- **Configurable Metrics:** Easily extend or modify the list of metrics in `config.py` to fit your team’s needs.
- **Flexible Reviewer Mapping:** Assign specific review responsibilities via the configuration.
- **Database Storage:** All review data is securely stored in a local SQLite database (`sprint_06-06-2024.db` by default).

### 🔒 Access & Security

- **Browser-specific sessions:** Prevents multiple logins with the same reviewer identity and restricts review access appropriately.

---

## 🧰 Framework Extensibility

- Add new metrics or update the review structure by editing `config.py`.
- Extend database schema for advanced analytics or reporting.

---

## 🛠️ Contributing

Contributions, bug reports, and suggestions are welcome! Fork the repository and submit a pull request to get involved.

---

## 📝 Example Metrics

The default metrics include:

- Code Quality Metrics
- Development Efficiency
- Collaboration & Communication
- Learning and Growth
- Task and Time Management
- Customer/End-User Focus
- Innovation and Initiative
- Consistency and Reliability
- Team Support & Mentorship
- Work-Life Balance

Modify these in `config.py` as per your review workflow.

---

## 📌 Note

- This tool is intended for internal team use.
- Ensure that you run the app via Streamlit as direct execution with Python is not supported.
- Currently, clearing cache on the browser will lock one out, once signed in, so currently avoid doing that.
- Private browsing may also lead to the above mentioned issue, and currently, the tab needs a refresh to start working due to cache unavailable for the first time
