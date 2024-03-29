# Proxy
A proxy to gate API for authorized Google user accounts.


## To start
```
./start.sh
```

## To install:
```
$pip3 install -r requirements.txt
```

**Note**: `lib/config.py` is rquired:
```
$mv lib/config.example.py lib/config.py
```
and replce all "\<hide\>" with you own settings.


## Dev Runbook
```
$cd proxy/
python3 main.py
```
and output like:
```
INFO:     Started server process [22228]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on https://127.0.0.1:8000 (Press CTRL+C to quit)
```

Open `https://127.0.0.1:8000` with your brower to check out the example UI.
Open `https://127.0.0.1:8000/docs` to checkout the fastAPI API docoments. 



To connect with the DB 
```bash
$ db_file=$(cat lib/config.py | grep SQLITE_DB_FILE | awk -F'"' '{print $2}') ; sqlite3 $db_file
```