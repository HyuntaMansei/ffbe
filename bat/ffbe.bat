set root=C:\Users\jchoi\anaconda3
call %root%\Scripts\activate.bat %root%

call conda env list
call conda activate py311
call cd C:\Users\jchoi\Coding\python\ffbe
call python ffbe_gui.py

pause