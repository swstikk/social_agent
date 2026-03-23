# Instagram Automation Testing

To test the instagram automation features on your local machine, run the test script `test_insta.py` and provide your instagram `sessionid` cookie as an environment variable.

```bash
# First, ensure dependencies are installed
pip install pytest-playwright playwright requests
playwright install chromium

# Run the test script with your session ID
export INSTA_SESSION_ID="YOUR_SESSION_ID_HERE"
python test_insta.py
```
