# Preview of project #
## 1. Main page ##
<img width="1745" height="746" alt="image" src="https://github.com/user-attachments/assets/cd75fb6a-861a-41c3-9876-95adcf3de485" />

## 2. Login page ##
<img width="1749" height="629" alt="image" src="https://github.com/user-attachments/assets/621e774f-1cc1-46fa-a0f2-7759ef130ed4" />

## 3. Channel page ##
<img width="1355" height="603" alt="image" src="https://github.com/user-attachments/assets/c5871002-1bd6-4d84-ac14-5ed57d56a501" />

# Server testing phase #
# 1.Terminal #
Connection to server [done] <br>
Authentication to server [done] <br>
Receving messages from clients [done] <br>
Sending messages to clients [in progress] <br>
# 2.Graphical Interface #
Connection to server [done] <br>
Authentication to server [done] <br>
Receving messages from clients [done] <br>
Sending messages to clients [in progress] <br>

# Installation and opening project in web #
Required Python - 3.11 or newer

```bash
python -m venv venv
source venv/bin/active #in Windows . venv/Scripts/activate
pip install -r requirements.txt
python discord_clone/manage.py migrate
#In 2 separate terminals
python discord_clone/manage.py runserver
python discord_clone/manage.py tcp_client 
