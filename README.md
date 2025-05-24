# Royal Mail Tracker GUI (PySide6 + Selenium)

This is a Python desktop application that automates the process of checking tracking codes on the Royal Mail website.

## 🔧 What it does

- Accepts a `.txt` file with tracking codes (one per line)
- Splits the list into batches of **500 codes**
- For each batch:
  - Opens a new browser window
  - Processes the codes
  - Closes the browser
- This simulates **human-like behavior** to avoid detection
- Results are saved in a `.csv` file inside a `done/` folder
- You can choose to automatically open the file when done

## 🖥️ Interface features

- Built with **PySide6**
- Progress bar and status updates per batch
- Option to open the result file automatically
- Help button explaining how it works

## ▶️ How to run

```bash
pip install -r requirements.txt
python main.py
```

### Requirements:
- Python 3.8+
- PySide6
- selenium
- selenium-stealth
- Chrome + chromedriver (must be compatible)

## 📁 Output

A file like `results_24052025_183101.csv` will be saved in a `done/` folder.

## 🧠 Tip

To avoid being blocked by Royal Mail, the program waits random delays between requests and opens/closes the browser at each batch.

---

MIT License.
