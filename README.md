# python_ppm_criterion_highlight_system
Running automatic ppm criterion highlight system with FASTAPI

_© 2022 Dante
## Installation and Execution

### environment
python version: v3.7, or you choose v3.8 - v3.10

### 1. Run docker
If you don't have MsSQL and MySQL DB,
you can run `docker-compose up.py` to start MySQL and MsSQL database and close it by `docker-compose down`

### 2. Run virtual environment and install package
run `./venv/Script/activate` to start virtual environment or close it by `deactivate`,
then please run `python -m pip install --upgrade pip` first,
then run `pip install -r requirement.txt`

### 3. Set up base Information
put your base information such as `database`, `file_path`, `email` info to `ppm_config.ini` file

### 4. Run FastAPI service
run `python main.py` start FASTAPI service,
or you can try another way with command line
run `uvicorn main:app --reload --host 0.0.0.0 --port 8003`
PS: If you run `python main.py`, the program will run test first then run system, 
you can find the test report in the folder `report/report.html`.

### 5. Check API Document
If server run correctly, check the API document on `http://127.0.0.1:8003/docs`
or you can check it by txt file by `http://127.0.0.1:8003/redoc`

### 6. Package to private network
If you want to run it on private network or close environment, run `pyinstaller -F main.py`
then take `main.exe` from `dict` folder and copy `idenprof` at same folder.
Note!: Before you package, please mark `pytest main()` in __main__, otherwise the .exe file would run fail.