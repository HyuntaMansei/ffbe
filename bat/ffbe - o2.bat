set root=C:\ProgramData\
call %root%\anaconda3\Scripts\activate.bat %root%\anaconda3
call conda activate py311
call cd D:\ProgramFiles\ffbe
call python ffbe_gui.py

pause